"""Dedicated connector-ingestion worker orchestration."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import socket
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic
from typing import Protocol

from redis.asyncio import Redis
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.configuration.schemas.settings import AppSettings, get_settings
from ecms.connectors.ingestion.git_runtime import (
    GitCommandRunner,
    GitLimits,
    GitWorkspace,
    IngestionCancelledError,
)
from ecms.connectors.ingestion.queue import IngestionJob, IngestionQueue
from ecms.connectors.ingestion.scanner import ScanLimits, ScannedFile, scan_repository
from ecms.persistence.database.rest_session import db_session
from ecms.persistence.models.connector_ingestion_job import ConnectorIngestionJob
from ecms.persistence.repositories.knowledge_graph_snapshot import (
    KnowledgeGraphSnapshotRepository,
)
from ecms.shared.time import utcnow
from ecms.visualization.graph_changed import snapshot_after_graph_write

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GitJobSpec:
    """Decrypted job input loaded from durable persistence."""

    job_id: str
    organization_id: str
    repo_url: str
    branch: str
    connection_id: int
    access_token: str | None = None
    requested_revision: str | None = None
    resolved_revision: str | None = None
    last_successful_revision: str | None = None
    checkpoint_files: int = 0
    checkpoint_nodes: int = 0
    checkpoint_edges: int = 0
    workspace_id: str | None = None


@dataclass(frozen=True)
class ChunkWrite:
    """Graph counters committed by one chunk."""

    nodes: int
    edges: int = 0


class JobStore(Protocol):
    """Persistence boundary implemented by the connector job domain service."""

    async def claim(self, job_id: str, organization_id: str) -> GitJobSpec | None: ...  # noqa: D102
    async def cancellation_requested(self, job_id: str) -> bool: ...  # noqa: D102
    async def renew_lease(self, job_id: str) -> bool: ...  # noqa: D102
    async def mark_stage(self, job_id: str, stage: str) -> None: ...  # noqa: D102
    async def record_revision(self, job_id: str, revision: str) -> None: ...  # noqa: D102
    async def checkpoint(  # noqa: D102
        self,
        job_id: str,
        *,
        files_processed: int,
        nodes_written: int,
        edges_written: int,
    ) -> None: ...
    async def complete(self, job_id: str) -> None: ...  # noqa: D102
    async def cancel(self, job_id: str) -> None: ...  # noqa: D102
    async def fail(self, job_id: str, error: str, *, retrying: bool) -> None: ...  # noqa: D102


class ChunkSink(Protocol):
    """Incremental graph writer; implementations must make chunks idempotent."""

    async def write(  # noqa: D102
        self, spec: GitJobSpec, files: Sequence[ScannedFile]
    ) -> ChunkWrite: ...
    async def finalize(self, spec: GitJobSpec) -> None: ...  # noqa: D102


class IngestionWorker:
    """Process one delivery with cancellation, checkpoints and bounded memory."""

    def __init__(
        self,
        *,
        queue: IngestionQueue,
        store: JobStore,
        sink: ChunkSink,
        settings: AppSettings,
    ) -> None:
        """Compose queue, persistence, Git and graph boundaries."""
        self._queue = queue
        self._store = store
        self._sink = sink
        self._settings = settings
        self._workspace = GitWorkspace(
            GitCommandRunner(),
            GitLimits(
                clone_timeout_seconds=settings.connector_git_clone_timeout_seconds,
                fetch_timeout_seconds=settings.connector_git_fetch_timeout_seconds,
                clone_depth=settings.connector_git_clone_depth,
            ),
        )

    async def process(self, delivery: IngestionJob) -> None:
        """Process one durable stream delivery."""
        spec = await self._store.claim(delivery.job_id, delivery.organization_id)
        if spec is None:
            await self._queue.acknowledge(delivery)
            return
        cancel = asyncio.Event()
        cancellation_poll = asyncio.create_task(self._poll_cancellation(spec.job_id, cancel))
        try:
            await self._store.mark_stage(spec.job_id, "cloning")
            repository = await self._workspace.prepare(
                repo_url=spec.repo_url,
                branch=spec.branch,
                destination=(
                    Path(self._settings.connector_ingestion_workspace)
                    / spec.organization_id
                    / spec.job_id
                ),
                cancel=cancel,
                access_token=spec.access_token,
            )
            revision = await self._workspace.current_revision(
                repository,
                cancel=cancel,
            )
            await self._store.record_revision(spec.job_id, revision)
            spec = replace(spec, resolved_revision=revision)
            if revision == spec.last_successful_revision:
                logger.info(
                    "connector ingestion revision unchanged",
                    extra={
                        "job_id": spec.job_id,
                        "organization_id": spec.organization_id,
                        "connection_id": spec.connection_id,
                        "revision": revision,
                    },
                )
                await self._store.complete(spec.job_id)
                await self._acknowledge_best_effort(delivery)
                return
            await self._store.mark_stage(spec.job_id, "scanning")
            processed = 0
            nodes_written = spec.checkpoint_nodes
            edges_written = spec.checkpoint_edges
            async for chunk in scan_repository(
                repository,
                limits=ScanLimits(
                    chunk_size=self._settings.connector_ingestion_chunk_size,
                    max_files=self._settings.connector_ingestion_max_files,
                    max_file_bytes=self._settings.connector_ingestion_max_file_bytes,
                    max_total_bytes=self._settings.connector_ingestion_max_total_bytes,
                ),
                cancel=cancel,
            ):
                # Checkpoint semantics intentionally replay the current chunk after a crash.
                # Sinks must use stable (job, relative_path) idempotency keys.
                if processed + len(chunk) <= spec.checkpoint_files:
                    processed += len(chunk)
                    continue
                await self._store.mark_stage(spec.job_id, "writing")
                write_started = monotonic()
                written = await self._sink.write(spec, chunk)
                try:
                    await self._queue.set_metric(
                        "graph_write_seconds_last", monotonic() - write_started
                    )
                except Exception:
                    logger.warning(
                        "connector ingestion metric update failed",
                        extra={"job_id": spec.job_id},
                    )
                processed += len(chunk)
                nodes_written += written.nodes
                edges_written += written.edges
                await self._store.checkpoint(
                    spec.job_id,
                    files_processed=processed,
                    nodes_written=nodes_written,
                    edges_written=edges_written,
                )
                await asyncio.sleep(
                    self._settings.connector_ingestion_write_yield_seconds
                )
            if cancel.is_set():
                raise IngestionCancelledError("ingestion cancelled")
            await self._store.mark_stage(spec.job_id, "snapshotting")
            await self._sink.finalize(spec)
            await self._store.complete(spec.job_id)
            await self._acknowledge_best_effort(delivery)
        except IngestionCancelledError:
            await self._store.cancel(spec.job_id)
            await self._acknowledge_best_effort(delivery)
        except Exception as exc:
            try:
                retrying = await self._queue.retry_or_exhaust(
                    delivery,
                    max_deliveries=self._settings.connector_ingestion_max_deliveries,
                )
            except Exception:
                # The unacknowledged stream delivery remains durable and will be
                # reclaimed after Redis recovers.
                retrying = True
            await self._store.fail(spec.job_id, _safe_error(exc), retrying=retrying)
            raise
        finally:
            cancellation_poll.cancel()
            await asyncio.gather(cancellation_poll, return_exceptions=True)

    async def _acknowledge_best_effort(self, delivery: IngestionJob) -> None:
        """Keep a durable terminal database state authoritative during Redis outages."""
        try:
            await self._queue.acknowledge(delivery)
        except Exception:
            logger.warning(
                "connector ingestion acknowledgement deferred",
                extra={"job_id": delivery.job_id},
            )

    async def _poll_cancellation(
        self, job_id: str, cancellation: asyncio.Event
    ) -> None:
        while not cancellation.is_set():
            if not await self._store.renew_lease(job_id):
                cancellation.set()
                return
            if await self._store.cancellation_requested(job_id):
                cancellation.set()
                return
            await asyncio.sleep(2)


async def _worker_loop(
    queue: IngestionQueue, worker: IngestionWorker
) -> None:
    while True:
        delivery = await queue.read()
        await queue.heartbeat()
        if delivery is None:
            delivery = await queue.claim_stale(
                min_idle_ms=worker._settings.connector_ingestion_stale_after_seconds
                * 1_000
            )
            if delivery is None:
                continue
        try:
            await worker.process(delivery)
            await queue.increment_metric("jobs_completed")
        except Exception:
            await queue.increment_metric("jobs_failed")
            logger.exception("connector ingestion failed for job %s", delivery.job_id)
            await asyncio.sleep(2)


def _safe_error(exc: Exception) -> str:
    """Bound persisted errors and avoid accidentally retaining secret-rich messages."""
    return f"{type(exc).__name__}: {exc}"[:2_000]


class PostgresJobStore:
    """Persist worker lifecycle and checkpoints in short transactions."""

    def __init__(self, *, lease_owner: str, lease_seconds: int = 120) -> None:
        """Bind a stable identity used to audit job ownership."""
        self._lease_owner = lease_owner
        self._lease_seconds = lease_seconds

    async def claim(
        self, job_id: str, organization_id: str
    ) -> GitJobSpec | None:
        """Claim an eligible job and return its credential-free source specification."""
        async with db_session() as session:
            result = await session.execute(
                select(ConnectorIngestionJob)
                .where(
                    ConnectorIngestionJob.id == job_id,
                    ConnectorIngestionJob.organization_id == organization_id,
                )
                .with_for_update()
            )
            job = result.scalar_one_or_none()
            if job is None or job.state in {"ready", "cancelled"}:
                return None
            if job.state == "cancel_requested":
                job.state = job.stage = "cancelled"
                job.completed_at = utcnow()
                await self._sync_connection(session, job)
                return None
            now = utcnow()
            lease_expires_at = job.lease_expires_at
            if lease_expires_at and lease_expires_at.tzinfo is None:
                lease_expires_at = lease_expires_at.replace(tzinfo=UTC)
            lease_is_current = bool(lease_expires_at and lease_expires_at > now)
            # A redelivered job can be recovered after its previous lease expires.
            if (
                job.state not in {"queued", "retrying", "failed"}
                and job.lease_owner not in {None, self._lease_owner}
                and lease_is_current
            ):
                return None
            job.state = job.stage = "validating"
            job.started_at = job.started_at or now
            job.lease_owner = self._lease_owner
            job.lease_expires_at = now + timedelta(seconds=self._lease_seconds)
            job.error_code = None
            job.error_summary = None
            job.updated_at = now
            await self._sync_connection(session, job)
            checkpoint = job.checkpoint or {}
            last_successful_revision = await session.scalar(
                text(
                    "SELECT last_successful_revision FROM connections "
                    "WHERE number = :connection_id"
                ),
                {"connection_id": job.connection_id},
            )
            return GitJobSpec(
                job_id=job.id,
                organization_id=job.organization_id,
                repo_url=job.repository_url,
                branch=job.branch,
                connection_id=job.connection_id,
                requested_revision=job.requested_revision,
                resolved_revision=job.resolved_revision,
                last_successful_revision=last_successful_revision,
                checkpoint_files=int(checkpoint.get("files_processed", 0)),
                checkpoint_nodes=job.nodes_written,
                checkpoint_edges=job.edges_written,
                workspace_id=job.workspace_id,
            )

    async def cancellation_requested(self, job_id: str) -> bool:
        """Read the durable cancellation flag."""
        async with db_session() as session:
            value = await session.scalar(
                select(ConnectorIngestionJob.cancellation_requested).where(
                    ConnectorIngestionJob.id == job_id
                )
            )
            return bool(value)

    async def renew_lease(self, job_id: str) -> bool:
        """Extend this worker's durable lease; false means ownership was lost."""
        async with db_session() as session:
            job = await session.get(ConnectorIngestionJob, job_id)
            if (
                job is None
                or job.lease_owner != self._lease_owner
                or job.state in {"ready", "failed", "cancelled"}
            ):
                return False
            now = utcnow()
            job.lease_expires_at = now + timedelta(seconds=self._lease_seconds)
            job.updated_at = now
            return True

    async def mark_stage(self, job_id: str, stage: str) -> None:
        """Advance through every legal intermediate lifecycle state."""
        paths = {
            "cloning": ("cloning",),
            "scanning": ("scanning",),
            "writing": ("extracting", "writing"),
            "snapshotting": ("snapshotting",),
        }
        async with db_session() as session:
            job = await session.get(ConnectorIngestionJob, job_id)
            if job is None:
                raise RuntimeError("ingestion job disappeared")
            for target in paths[stage]:
                if job.state == target:
                    continue
                job.state = job.stage = target
                job.updated_at = utcnow()
            await self._sync_connection(session, job)

    async def record_revision(self, job_id: str, revision: str) -> None:
        """Persist the immutable source revision before scanning begins."""
        async with db_session() as session:
            job = await session.get(ConnectorIngestionJob, job_id)
            if job is None:
                raise RuntimeError("ingestion job disappeared")
            job.resolved_revision = revision
            job.updated_at = utcnow()

    async def checkpoint(
        self,
        job_id: str,
        *,
        files_processed: int,
        nodes_written: int,
        edges_written: int,
    ) -> None:
        """Record a committed chunk boundary for idempotent restart."""
        async with db_session() as session:
            job = await session.get(ConnectorIngestionJob, job_id)
            if job is None:
                raise RuntimeError("ingestion job disappeared")
            job.files_processed = files_processed
            job.files_discovered = max(job.files_discovered, files_processed)
            job.nodes_written = nodes_written
            job.edges_written = edges_written
            job.checkpoint = {"files_processed": files_processed}
            denominator = max(job.files_discovered, files_processed + 1)
            job.progress_percent = min(90, 10 + int(80 * files_processed / denominator))
            job.updated_at = utcnow()

    async def complete(self, job_id: str) -> None:
        """Mark a fully snapshotted job ready."""
        await self._terminal(job_id, "ready")

    async def cancel(self, job_id: str) -> None:
        """Mark a cooperatively cancelled job terminal."""
        await self._terminal(job_id, "cancelled")

    async def fail(self, job_id: str, error: str, *, retrying: bool) -> None:
        """Persist a safe failure summary and whether delivery will retry."""
        async with db_session() as session:
            job = await session.get(ConnectorIngestionJob, job_id)
            if job is None:
                return
            job.state = job.stage = "retrying" if retrying else "failed"
            job.error_code = "INGESTION_WORKER_FAILED"
            job.error_summary = error
            job.lease_owner = None
            job.lease_expires_at = None
            job.updated_at = utcnow()
            if not retrying:
                job.completed_at = utcnow()
            await self._sync_connection(session, job)

    async def _terminal(self, job_id: str, state: str) -> None:
        async with db_session() as session:
            job = await session.get(ConnectorIngestionJob, job_id)
            if job is None:
                return
            job.state = job.stage = state
            job.progress_percent = 100 if state == "ready" else job.progress_percent
            job.completed_at = utcnow()
            job.lease_owner = None
            job.lease_expires_at = None
            job.updated_at = utcnow()
            snapshot_version: str | None = None
            if state == "ready":
                snapshot = await KnowledgeGraphSnapshotRepository(session).get_current(
                    job.organization_id
                )
                snapshot_version = snapshot.version if snapshot else None
            await self._sync_connection(session, job)
            if state == "ready":
                await session.execute(
                    text(
                        "UPDATE connections SET last_successful_revision = :revision, "
                        "last_successful_snapshot_version = :snapshot_version "
                        "WHERE number = :connection_id"
                    ),
                    {
                        "revision": job.resolved_revision,
                        "snapshot_version": snapshot_version,
                        "connection_id": job.connection_id,
                    },
                )

    @staticmethod
    async def _sync_connection(
        session: AsyncSession, job: ConnectorIngestionJob
    ) -> None:
        await session.execute(
            text(
                "UPDATE connections SET current_ingestion_job_id = :job_id, "
                "sync_state = :sync_state, last_error_summary = :error "
                "WHERE number = :connection_id"
            ),
            {
                "job_id": job.id,
                "sync_state": job.state,
                "error": job.error_summary,
                "connection_id": job.connection_id,
            },
        )


class LegacyGraphChunkSink:
    """Write bounded chunks through the existing graph pipeline."""

    def __init__(self, *, snapshot_timeout_seconds: int = 1_800) -> None:
        """Track successful writes for snapshot gating."""
        self._successes: dict[str, int] = {}
        self._snapshot_timeout_seconds = snapshot_timeout_seconds

    async def write(
        self, spec: GitJobSpec, files: Sequence[ScannedFile]
    ) -> ChunkWrite:
        """Normalize a file chunk and submit one graph batch."""
        from legacy_ecms.api.graph_context import orchestrator_context
        from legacy_ecms.core.uko import UKOMetadata, UKOType, UniversalKnowledgeObject
        from legacy_ecms.pipeline.workspace import attach_ukos_to_workspace

        now = datetime.now(UTC)
        ukos = [
            UniversalKnowledgeObject(
                id=f"git:file:{_repository_name(spec.repo_url)}:{item.relative_path}",
                type=_uko_type(item.relative_path, UKOType),
                name=item.relative_path,
                content=item.content,
                metadata=UKOMetadata(
                    source="git",
                    source_id=item.relative_path,
                    source_url=spec.repo_url,
                    created_at=now,
                    modified_at=now,
                    tags=[Path(item.relative_path).suffix.lower().lstrip(".")],
                    tenant_id=spec.organization_id,
                ),
                raw_data={
                    "repo_url": spec.repo_url,
                    "path": item.relative_path,
                    "size_bytes": item.size_bytes,
                    "organization_id": spec.organization_id,
                    "connection_id": str(spec.connection_id),
                    "ingestion_revision": spec.resolved_revision or spec.job_id,
                },
                ingestion_batch_id=spec.job_id,
            )
            for item in files
        ]
        if spec.workspace_id:
            ukos = attach_ukos_to_workspace(
                ukos, spec.workspace_id, spec.workspace_id
            )
        async with orchestrator_context(True) as orchestrator:
            _, result = await orchestrator.process_batch(ukos)
        if result.failure_count:
            first = result.failures[0]
            raise RuntimeError(
                f"graph batch failed ({result.failure_count}): {first.error_message}"
            )
        self._successes[spec.job_id] = (
            self._successes.get(spec.job_id, 0) + result.success_count
        )
        return ChunkWrite(nodes=result.success_count)

    async def finalize(self, spec: GitJobSpec) -> None:
        """Request and wait for the immutable snapshot containing this revision."""
        success_count = self._successes.get(spec.job_id, 0)
        if success_count <= 0:
            raise RuntimeError("repository produced no graph nodes")
        await asyncio.to_thread(self._retire_stale_revision, spec)
        await snapshot_after_graph_write(
            persisted=True,
            success_count=success_count,
            source="git",
            revision=spec.job_id,
            organization_id=spec.organization_id,
        )
        expected_watermark = f"git:{spec.job_id}"
        deadline = monotonic() + self._snapshot_timeout_seconds
        while monotonic() < deadline:
            async with db_session() as session:
                repository = KnowledgeGraphSnapshotRepository(session)
                current = await repository.get_current(spec.organization_id)
                if current and current.source_watermark == expected_watermark:
                    return
                latest = await repository.get_latest(spec.organization_id)
                if (
                    latest
                    and latest.source_watermark == expected_watermark
                    and latest.state == "failed"
                ):
                    raise RuntimeError(
                        f"knowledge graph snapshot failed: "
                        f"{latest.error_summary or 'unknown error'}"
                    )
            await asyncio.sleep(2)
        raise TimeoutError(
            f"knowledge graph snapshot did not activate within "
            f"{self._snapshot_timeout_seconds}s"
        )

    async def finalize_persisted(
        self, spec: GitJobSpec, *, success_count: int
    ) -> None:
        """Finalize graph writes recovered from durable batch counters."""
        if success_count < 1:
            raise ValueError("success_count must be positive")
        self._successes[spec.job_id] = max(
            self._successes.get(spec.job_id, 0), success_count
        )
        await self.finalize(spec)

    @staticmethod
    def _retire_stale_revision(spec: GitJobSpec) -> None:
        """Delete files removed from this connection after the new revision is complete."""
        import falkordb
        from legacy_ecms.config import get_settings as get_legacy_settings

        settings = get_legacy_settings()
        database = falkordb.FalkorDB(
            host=settings.falkordb_host,
            port=settings.falkordb_port,
            password=settings.falkordb_password or None,
        )
        graph = database.select_graph(settings.falkordb_database)
        parameters = {
            "organization_id": spec.organization_id,
            "connection_id": str(spec.connection_id),
            "revision": spec.resolved_revision or spec.job_id,
            "batch_size": 10_000,
        }
        while True:
            result = graph.query(
                "MATCH (u:UKO) "
                "WHERE u.organization_id = $organization_id "
                "AND u.connection_id = $connection_id "
                "AND u.ingestion_revision <> $revision "
                "WITH u LIMIT $batch_size "
                "DETACH DELETE u "
                "RETURN count(*)",
                parameters,
            )
            rows = result.result_set if hasattr(result, "result_set") else result
            deleted = int(rows[0][0]) if rows and rows[0] else 0
            if deleted < parameters["batch_size"]:
                return


def _repository_name(repo_url: str) -> str:
    readable = repo_url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    digest = hashlib.sha256(repo_url.encode()).hexdigest()[:12]
    return f"{readable}-{digest}"


def _uko_type(path: str, enum: object) -> object:
    suffix = Path(path).suffix.lower()
    if suffix in {".md", ".markdown"}:
        return enum.DOCUMENT
    return enum.FILE


async def run_worker(
    store: JobStore | None = None, sink: ChunkSink | None = None
) -> None:
    """Run the production worker or injected test adapters."""
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    consumer = f"{socket.gethostname()}-{os.getpid()}"
    queue = IngestionQueue(redis, consumer=consumer)
    await queue.ensure_group()
    await queue.heartbeat()
    try:
        await _worker_loop(
            queue,
            IngestionWorker(
                queue=queue,
                store=store
                or PostgresJobStore(
                    lease_owner=consumer,
                    lease_seconds=settings.connector_ingestion_stale_after_seconds,
                ),
                sink=sink
                or LegacyGraphChunkSink(
                    snapshot_timeout_seconds=(
                        settings.connector_ingestion_snapshot_timeout_seconds
                    )
                ),
                settings=settings,
            ),
        )
    finally:
        await redis.aclose()


def main() -> None:
    """Start the dedicated connector-ingestion worker."""
    logging.basicConfig(level=os.environ.get("ECMS_LOG_LEVEL", "INFO"))
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
