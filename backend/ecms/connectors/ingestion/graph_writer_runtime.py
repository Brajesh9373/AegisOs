"""Persistence-aware graph writer and atomic fan-in runtime."""

from __future__ import annotations

import asyncio
import gzip
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol, cast

from sqlalchemy import func, select, text

from ecms.connectors.ingestion.fan_in import reconcile_fan_in
from ecms.connectors.ingestion.graph_semaphore import (
    GraphWriteLease,
    GraphWriteSemaphore,
)
from ecms.connectors.ingestion.parallel_queue import GraphWriteDelivery
from ecms.connectors.ingestion.scanner import ScannedFile
from ecms.connectors.ingestion.worker import (
    GitJobSpec,
    LegacyGraphChunkSink,
)
from ecms.infrastructure.storage.object_store import ObjectStore
from ecms.persistence.database.rest_session import db_session
from ecms.persistence.models.connector_ingestion_job import ConnectorIngestionJob
from ecms.persistence.models.connector_ingestion_partition import (
    ConnectorIngestionManifest,
    ConnectorIngestionPartition,
    ConnectorIngestionStageBatch,
)
from ecms.persistence.repositories.connector_ingestion_partition import (
    ConnectorIngestionPartitionRepository,
    ConnectorIngestionStageBatchRepository,
)
from ecms.persistence.repositories.knowledge_graph_snapshot import (
    KnowledgeGraphSnapshotRepository,
)
from ecms.shared.time import utcnow


class GraphWriteCancelledError(RuntimeError):
    """A parent cancellation or lost lease stopped a graph write."""


@dataclass(frozen=True, slots=True)
class GraphBatchWork:
    """Tenant-scoped durable metadata for one staged graph batch."""

    batch_id: str
    partition_id: str
    manifest_id: str
    job_id: str
    organization_id: str
    object_key: str
    checksum: str
    byte_count: int
    node_count: int
    edge_count: int
    sequence_number: int
    spec: GitJobSpec
    already_committed: bool = False


@dataclass(frozen=True, slots=True)
class DecodedGraphBatch:
    """Validated bounded payload ready for the legacy graph sink."""

    files: tuple[ScannedFile, ...]
    node_count: int
    edge_count: int


@dataclass(frozen=True, slots=True)
class PublicationWork:
    """The one durable snapshot publication claimed for a parent job."""

    spec: GitJobSpec
    success_count: int


class GraphBatchStore(Protocol):
    """Short-transaction persistence boundary for graph writes."""

    async def claim(  # noqa: D102
        self, delivery: GraphWriteDelivery, writer_id: str
    ) -> GraphBatchWork | None: ...
    async def renew(self, work: GraphBatchWork, writer_id: str) -> bool: ...  # noqa: D102
    async def cancellation_requested(self, work: GraphBatchWork) -> bool: ...  # noqa: D102
    async def commit(self, work: GraphBatchWork, writer_id: str) -> None: ...  # noqa: D102
    async def retry(  # noqa: D102
        self, work: GraphBatchWork, writer_id: str, error: Exception
    ) -> None: ...
    async def reconcile(  # noqa: D102
        self, work: GraphBatchWork, writer_id: str
    ) -> PublicationWork | None: ...
    async def publication_complete(  # noqa: D102
        self, publication: PublicationWork, writer_id: str
    ) -> None: ...
    async def publication_failed(  # noqa: D102
        self, publication: PublicationWork, writer_id: str, error: Exception
    ) -> None: ...
    async def exhausted(  # noqa: D102
        self, delivery: GraphWriteDelivery, error: Exception
    ) -> None: ...


class PostgresGraphBatchStore:
    """Durably lease batches and serialize parent snapshot publication."""

    def __init__(self, *, lease_seconds: int = 120) -> None:
        """Configure recoverable database lease duration."""
        self._lease_seconds = max(lease_seconds, 1)

    async def claim(self, delivery: GraphWriteDelivery, writer_id: str) -> GraphBatchWork | None:
        """Claim exactly the delivered batch and validate all provenance IDs."""
        async with db_session() as session:
            batch = await session.scalar(
                select(ConnectorIngestionStageBatch)
                .where(
                    ConnectorIngestionStageBatch.id == delivery.stage_batch_id,
                    ConnectorIngestionStageBatch.job_id == delivery.job_id,
                    ConnectorIngestionStageBatch.partition_id == delivery.partition_id,
                )
                .with_for_update()
            )
            if batch is None:
                return None
            partition = await session.get(ConnectorIngestionPartition, batch.partition_id)
            job = await session.get(ConnectorIngestionJob, batch.job_id)
            if (
                partition is None
                or job is None
                or partition.organization_id != batch.organization_id
                or job.organization_id != batch.organization_id
            ):
                raise ValueError("staged batch provenance is inconsistent")
            manifest = await session.get(ConnectorIngestionManifest, partition.manifest_id)
            if manifest is None or manifest.resolved_revision != job.resolved_revision:
                raise ValueError("staged batch manifest revision is inconsistent")
            spec = _job_spec(job)
            if batch.state == "committed":
                return _batch_work(
                    batch,
                    spec,
                    manifest_id=partition.manifest_id,
                    already_committed=True,
                )
            if job.state in {"cancel_requested", "cancelled"}:
                batch.state = "cancelled"
                batch.writer_owner = None
                batch.writer_lease_expires_at = None
                return None
            now = utcnow()
            expiry = _aware(batch.writer_lease_expires_at)
            claimable = batch.state == "staged" or (
                batch.state == "writing" and expiry is not None and expiry <= now
            )
            owned = batch.state == "writing" and batch.writer_owner == writer_id
            if not claimable and not owned:
                return None
            batch.state = "writing"
            batch.writer_owner = writer_id
            batch.writer_lease_expires_at = now + timedelta(seconds=self._lease_seconds)
            if not owned:
                batch.attempt += 1
            batch.error_summary = None
            job.state = job.stage = "writing"
            return _batch_work(batch, spec, manifest_id=partition.manifest_id)

    async def renew(self, work: GraphBatchWork, writer_id: str) -> bool:
        """Renew only a currently owned writing lease."""
        async with db_session() as session:
            return await ConnectorIngestionStageBatchRepository(session).renew_lease(
                work.batch_id,
                organization_id=work.organization_id,
                writer_id=writer_id,
                lease_seconds=self._lease_seconds,
            )

    async def cancellation_requested(self, work: GraphBatchWork) -> bool:
        """Check tenant-scoped parent cancellation."""
        async with db_session() as session:
            state = await session.scalar(
                select(ConnectorIngestionJob.state).where(
                    ConnectorIngestionJob.id == work.job_id,
                    ConnectorIngestionJob.organization_id == work.organization_id,
                )
            )
            return state in {"cancel_requested", "cancelled"}

    async def commit(self, work: GraphBatchWork, writer_id: str) -> None:
        """Commit one batch and its partition only after complete batch fan-in."""
        if work.already_committed:
            return
        async with db_session() as session:
            batch = await session.get(ConnectorIngestionStageBatch, work.batch_id)
            if (
                batch is None
                or batch.writer_owner != writer_id
                or batch.state != "writing"
                or _lease_expired(batch.writer_lease_expires_at)
            ):
                raise GraphWriteCancelledError("durable graph batch lease was lost")
            await ConnectorIngestionStageBatchRepository(session).transition(
                batch, "committed", writer_id=writer_id
            )
            partition = await session.get(ConnectorIngestionPartition, work.partition_id)
            if partition is None:
                raise ValueError("graph batch partition disappeared")
            remaining = int(
                await session.scalar(
                    select(func.count(ConnectorIngestionStageBatch.id)).where(
                        ConnectorIngestionStageBatch.partition_id == work.partition_id,
                        ConnectorIngestionStageBatch.state != "committed",
                    )
                )
                or 0
            )
            if remaining == 0 and partition.state == "staged":
                await ConnectorIngestionPartitionRepository(session).transition(
                    partition, "committed"
                )

    async def retry(self, work: GraphBatchWork, writer_id: str, error: Exception) -> None:
        """Release an owned batch for bounded queue redelivery."""
        if work.already_committed:
            return
        async with db_session() as session:
            batch = await session.get(ConnectorIngestionStageBatch, work.batch_id)
            if batch is None or batch.writer_owner != writer_id or batch.state != "writing":
                return
            batch.state = "staged"
            batch.writer_owner = None
            batch.writer_lease_expires_at = None
            batch.error_summary = _safe_error(error)

    async def reconcile(self, work: GraphBatchWork, writer_id: str) -> PublicationWork | None:
        """Atomically claim the one parent snapshot after exact child fan-in."""
        async with db_session() as session:
            job = await session.scalar(
                select(ConnectorIngestionJob)
                .where(
                    ConnectorIngestionJob.id == work.job_id,
                    ConnectorIngestionJob.organization_id == work.organization_id,
                )
                .with_for_update()
            )
            if job is None:
                raise ValueError("parent ingestion job disappeared")
            if job.state in {"ready", "failed", "cancelled"} or (job.checkpoint or {}).get(
                "snapshot_completed"
            ):
                return None
            manifest = await session.scalar(
                select(ConnectorIngestionManifest).where(
                    ConnectorIngestionManifest.job_id == job.id,
                    ConnectorIngestionManifest.organization_id == job.organization_id,
                )
            )
            if manifest is None:
                raise ValueError("parent manifest disappeared")
            partition_summary = await ConnectorIngestionPartitionRepository(session).reconcile(
                job.id, job.organization_id
            )
            batch_summary = await ConnectorIngestionStageBatchRepository(session).reconcile(
                job.id, job.organization_id
            )
            decision = reconcile_fan_in(
                partition_states=partition_summary["states"],  # type: ignore[arg-type]
                batch_states=batch_summary["states"],  # type: ignore[arg-type]
                expected_partitions=manifest.partition_count,
            )
            if decision.terminal_failure:
                job.state = job.stage = "failed"
                job.error_code = "CONNECTOR_FAN_IN_FAILED"
                job.error_summary = decision.reason
                job.completed_at = utcnow()
                await session.execute(
                    text(
                        "UPDATE connections SET sync_state = 'failed', "
                        "last_error_summary = :error "
                        "WHERE number = :connection_id "
                        "AND current_ingestion_job_id = :job_id "
                        "AND (organization_id = :organization_id "
                        "OR organization_id IS NULL)"
                    ),
                    {
                        "connection_id": job.connection_id,
                        "job_id": job.id,
                        "organization_id": job.organization_id,
                        "error": decision.reason,
                    },
                )
                return None
            if not decision.ready_to_publish:
                return None
            checkpoint = job.checkpoint or {}
            expiry = _parse_checkpoint_time(checkpoint.get("snapshot_lease_expires_at"))
            owned = checkpoint.get("snapshot_owner") == writer_id
            claimable = job.state != "snapshotting" or expiry is None or expiry <= utcnow()
            if not owned and not claimable:
                return None
            job.state = job.stage = "snapshotting"
            job.lease_owner = writer_id
            job.lease_expires_at = utcnow() + timedelta(seconds=self._lease_seconds)
            job.files_processed = cast(int, partition_summary["files_processed"])
            job.nodes_written = cast(int, batch_summary["node_count"])
            job.edges_written = cast(int, batch_summary["edge_count"])
            job.progress_percent = 95
            job.checkpoint = {
                **checkpoint,
                "snapshot_owner": writer_id,
                "snapshot_lease_expires_at": job.lease_expires_at.isoformat(),
                "snapshot_watermark": f"git:{job.id}",
            }
            return PublicationWork(_job_spec(job), job.nodes_written)

    async def publication_complete(self, publication: PublicationWork, writer_id: str) -> None:
        """Mark the parent ready only after its exact snapshot is active."""
        async with db_session() as session:
            job = await session.get(ConnectorIngestionJob, publication.spec.job_id)
            if job is None or job.lease_owner != writer_id:
                raise GraphWriteCancelledError("snapshot publication lease was lost")
            job.state = job.stage = "ready"
            job.progress_percent = 100
            job.completed_at = utcnow()
            job.lease_owner = None
            job.lease_expires_at = None
            job.checkpoint = {
                **(job.checkpoint or {}),
                "snapshot_completed": True,
            }
            snapshot = await KnowledgeGraphSnapshotRepository(session).get_current(
                job.organization_id
            )
            await session.execute(
                text(
                    "UPDATE connections SET current_ingestion_job_id = :job_id, "
                    "sync_state = 'ready', last_error_summary = NULL, "
                    "last_successful_revision = :revision, "
                    "last_successful_snapshot_version = :snapshot_version "
                    "WHERE number = :connection_id "
                    "AND current_ingestion_job_id = :job_id "
                    "AND (organization_id = :organization_id "
                    "OR organization_id IS NULL)"
                ),
                {
                    "job_id": job.id,
                    "organization_id": job.organization_id,
                    "revision": job.resolved_revision,
                    "snapshot_version": snapshot.version if snapshot else None,
                    "connection_id": job.connection_id,
                },
            )

    async def publication_failed(
        self, publication: PublicationWork, writer_id: str, error: Exception
    ) -> None:
        """Release publication ownership for recovery without losing graph writes."""
        async with db_session() as session:
            job = await session.get(ConnectorIngestionJob, publication.spec.job_id)
            if job is None or job.lease_owner != writer_id:
                return
            job.lease_owner = None
            job.lease_expires_at = None
            job.error_summary = _safe_error(error)
            checkpoint = dict(job.checkpoint or {})
            checkpoint.pop("snapshot_owner", None)
            checkpoint.pop("snapshot_lease_expires_at", None)
            job.checkpoint = checkpoint

    async def exhausted(self, delivery: GraphWriteDelivery, error: Exception) -> None:
        """Make graph-write exhaustion durable and fail its parent partition."""
        async with db_session() as session:
            batch = await session.get(ConnectorIngestionStageBatch, delivery.stage_batch_id)
            if (
                batch is None
                or batch.job_id != delivery.job_id
                or batch.partition_id != delivery.partition_id
                or batch.state == "committed"
            ):
                return
            batch.state = "failed"
            batch.writer_owner = None
            batch.writer_lease_expires_at = None
            batch.error_summary = _safe_error(error)
            partition = await session.get(ConnectorIngestionPartition, delivery.partition_id)
            if partition is not None and partition.state not in {
                "committed",
                "cancelled",
                "superseded",
            }:
                partition.state = "failed"
                partition.lease_owner = None
                partition.lease_expires_at = None
                partition.error_summary = _safe_error(error)
                partition.completed_at = utcnow()
            job = await session.get(ConnectorIngestionJob, delivery.job_id)
            if job is not None:
                job.state = job.stage = "failed"
                job.error_code = "CONNECTOR_GRAPH_WRITE_EXHAUSTED"
                job.error_summary = _safe_error(error)
                job.completed_at = utcnow()


class GraphBatchHandler:
    """Validate, globally serialize, write, and reconcile one graph batch."""

    def __init__(
        self,
        *,
        store: GraphBatchStore,
        objects: ObjectStore,
        semaphore: GraphWriteSemaphore,
        sink: LegacyGraphChunkSink,
        writer_id: str,
        max_compressed_bytes: int = 64 * 1024 * 1024,
        max_decoded_bytes: int = 256 * 1024 * 1024,
        lease_poll_seconds: float = 2,
    ) -> None:
        """Configure strict memory ceilings and ownership boundaries."""
        self._store = store
        self._objects = objects
        self._semaphore = semaphore
        self._sink = sink
        self._writer_id = writer_id
        self._max_compressed_bytes = max_compressed_bytes
        self._max_decoded_bytes = max_decoded_bytes
        self._lease_poll_seconds = lease_poll_seconds

    async def __call__(self, delivery: GraphWriteDelivery) -> None:
        """Write one delivery; stream acknowledgement remains worker-owned."""
        work = await self._store.claim(delivery, self._writer_id)
        if work is None:
            return
        if not work.already_committed:
            try:
                decoded = await _load_batch(
                    self._objects,
                    work,
                    max_compressed_bytes=self._max_compressed_bytes,
                    max_decoded_bytes=self._max_decoded_bytes,
                )
                lease = await self._acquire_semaphore(work)
                try:
                    stop = asyncio.Event()
                    guard = asyncio.create_task(self._guard_leases(work, lease, stop))
                    try:
                        await self._sink.write(work.spec, decoded.files)
                        if stop.is_set():
                            raise GraphWriteCancelledError("graph write lease was lost")
                        await self._store.commit(work, self._writer_id)
                    finally:
                        stop.set()
                        guard.cancel()
                        await asyncio.gather(guard, return_exceptions=True)
                finally:
                    await self._semaphore.release(lease)
            except Exception as exc:
                await self._store.retry(work, self._writer_id, exc)
                raise

        publication = await self._store.reconcile(work, self._writer_id)
        if publication is None:
            return
        try:
            await self._sink.finalize_persisted(
                publication.spec,
                success_count=publication.success_count,
            )
            await self._store.publication_complete(publication, self._writer_id)
        except Exception as exc:
            await self._store.publication_failed(publication, self._writer_id, exc)
            raise

    async def _acquire_semaphore(self, work: GraphBatchWork) -> GraphWriteLease:
        while True:
            if await self._store.cancellation_requested(work):
                raise GraphWriteCancelledError("parent ingestion was cancelled")
            lease = await self._semaphore.acquire()
            if lease is not None:
                return lease
            if not await self._store.renew(work, self._writer_id):
                raise GraphWriteCancelledError("durable graph batch lease was lost")
            await asyncio.sleep(self._lease_poll_seconds)

    async def _guard_leases(
        self,
        work: GraphBatchWork,
        lease: GraphWriteLease,
        stop: asyncio.Event,
    ) -> None:
        while not stop.is_set():
            await asyncio.sleep(self._lease_poll_seconds)
            if (
                not await self._store.renew(work, self._writer_id)
                or not await self._semaphore.renew(lease)
                or await self._store.cancellation_requested(work)
            ):
                stop.set()
                return


async def _load_batch(
    objects: ObjectStore,
    work: GraphBatchWork,
    *,
    max_compressed_bytes: int,
    max_decoded_bytes: int,
) -> DecodedGraphBatch:
    info = await objects.stat_object(work.object_key)
    if info.size != work.byte_count:
        raise ValueError("staged object byte count does not match durable record")
    if info.size > max_compressed_bytes:
        raise ValueError("staged object exceeds compressed-byte ceiling")
    payload = await objects.get_object(work.object_key)
    canonical = await asyncio.to_thread(_bounded_gzip_decode, payload, max_decoded_bytes)
    if hashlib.sha256(canonical).hexdigest() != work.checksum:
        raise ValueError("staged object checksum does not match durable record")
    document = json.loads(canonical)
    _validate_document(document, work)
    nodes = document["nodes"]
    edges = document["edges"]
    if len(nodes) != work.node_count or len(edges) != work.edge_count:
        raise ValueError("staged object counters do not match durable record")
    if edges:
        raise ValueError("staged edge writes are not yet proven equivalent to the legacy pipeline")
    files: list[ScannedFile] = []
    seen: set[str] = set()
    for node in nodes:
        properties = node.get("properties")
        if not isinstance(properties, dict):
            raise ValueError("staged node properties are invalid")
        if properties.get("organization_id") != work.organization_id:
            raise ValueError("staged node tenant provenance is invalid")
        if properties.get("ingestion_revision") != work.spec.resolved_revision:
            raise ValueError("staged node revision provenance is invalid")
        path = properties.get("path")
        content = properties.get("content")
        size = properties.get("size_bytes")
        if (
            not isinstance(path, str)
            or not isinstance(content, str)
            or not isinstance(size, int)
            or path in seen
        ):
            raise ValueError("staged node file representation is invalid")
        encoded = content.encode("utf-8")
        if len(encoded) != size:
            raise ValueError("staged node file size is invalid")
        seen.add(path)
        files.append(ScannedFile(path, content, size))
    return DecodedGraphBatch(tuple(files), len(nodes), len(edges))


def _bounded_gzip_decode(payload: bytes, limit: int) -> bytes:
    with gzip.GzipFile(fileobj=io.BytesIO(payload), mode="rb") as stream:
        decoded = stream.read(limit + 1)
    if len(decoded) > limit:
        raise ValueError("staged object exceeds decoded-byte ceiling")
    return decoded


def _validate_document(document: Any, work: GraphBatchWork) -> None:
    if not isinstance(document, dict):
        raise ValueError("staged object must be a JSON object")
    expected = {
        "schema_version": 1,
        "job_id": work.job_id,
        "manifest_id": work.manifest_id,
        "partition_id": work.partition_id,
        "sequence_number": work.sequence_number,
    }
    if any(document.get(key) != value for key, value in expected.items()):
        raise ValueError("staged object provenance does not match delivery")
    if not isinstance(document.get("nodes"), list) or not isinstance(document.get("edges"), list):
        raise ValueError("staged object graph arrays are invalid")


def _batch_work(
    batch: ConnectorIngestionStageBatch,
    spec: GitJobSpec,
    *,
    manifest_id: str,
    already_committed: bool = False,
) -> GraphBatchWork:
    return GraphBatchWork(
        batch_id=batch.id,
        partition_id=batch.partition_id,
        manifest_id=manifest_id,
        job_id=batch.job_id,
        organization_id=batch.organization_id,
        object_key=batch.object_key,
        checksum=batch.checksum,
        byte_count=batch.byte_count,
        node_count=batch.node_count,
        edge_count=batch.edge_count,
        sequence_number=batch.sequence_number,
        spec=spec,
        already_committed=already_committed,
    )


def _job_spec(job: ConnectorIngestionJob) -> GitJobSpec:
    return GitJobSpec(
        job_id=job.id,
        organization_id=job.organization_id,
        repo_url=job.repository_url,
        branch=job.branch,
        connection_id=job.connection_id,
        requested_revision=job.requested_revision,
        resolved_revision=job.resolved_revision,
        workspace_id=job.workspace_id,
    )


def _aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _lease_expired(value: datetime | None) -> bool:
    aware = _aware(value)
    return aware is None or aware <= utcnow()


def _parse_checkpoint_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return _aware(datetime.fromisoformat(value))
    except ValueError:
        return None


def _safe_error(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"[:2_000]
