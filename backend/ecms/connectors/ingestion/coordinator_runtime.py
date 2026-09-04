"""Executable clone-once coordinator for partitioned connector ingestion."""

from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import logging
import tempfile
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from ecms.connectors.ingestion.coordinator import IngestionPlan, plan_repository
from ecms.connectors.ingestion.git_runtime import (
    GitWorkspace,
    IngestionCancelledError,
)
from ecms.connectors.ingestion.parallel_queue import ExtractionQueue
from ecms.connectors.ingestion.scanner import ScanLimits
from ecms.connectors.ingestion.worker import GitJobSpec, JobStore
from ecms.infrastructure.storage.object_store import ObjectStore
from ecms.persistence.database.rest_session import db_session
from ecms.persistence.models.connector_ingestion_job import ConnectorIngestionJob
from ecms.persistence.models.connector_ingestion_partition import (
    ConnectorIngestionManifest,
    ConnectorIngestionPartition,
)
from ecms.persistence.repositories.connector_ingestion_partition import (
    ConnectorIngestionManifestRepository,
    ConnectorIngestionPartitionRepository,
)

logger = logging.getLogger(__name__)
MANIFEST_FORMAT = "ecms.connector-manifest.v1"


@dataclass(frozen=True, slots=True)
class PersistedPartition:
    """Identifiers needed to publish one durable extraction partition."""

    partition_id: str
    manifest_id: str
    job_id: str


@dataclass(frozen=True, slots=True)
class CoordinationResult:
    """Observable outcome of coordinating one parent ingestion delivery."""

    status: str
    resolved_revision: str
    manifest_id: str | None = None
    manifest_checksum: str | None = None
    partition_count: int = 0


class CoordinatorPlanStore(Protocol):
    """Atomic persistence boundary for immutable plans."""

    async def persist(  # noqa: D102
        self,
        spec: GitJobSpec,
        *,
        revision: str,
        plan: IngestionPlan,
        object_key: str,
    ) -> Sequence[PersistedPartition]: ...


class PartitionPublisher(Protocol):
    """ID-only transport boundary used after the database commit."""

    async def enqueue(  # noqa: D102
        self, *, job_id: str, manifest_id: str, partition_id: str
    ) -> str: ...


class SqlCoordinatorPlanStore:
    """Persist a complete plan transactionally through ingestion repositories."""

    def __init__(
        self,
        session_factory: Callable[[], AbstractAsyncContextManager[AsyncSession]] = db_session,
    ) -> None:
        """Use short transaction-scoped sessions."""
        self._session_factory = session_factory

    async def persist(
        self,
        spec: GitJobSpec,
        *,
        revision: str,
        plan: IngestionPlan,
        object_key: str,
    ) -> Sequence[PersistedPartition]:
        """Create or recover an identical manifest and its partitions."""
        async with self._session_factory() as session:
            manifests = ConnectorIngestionManifestRepository(session)
            partitions = ConnectorIngestionPartitionRepository(session)
            existing = await manifests.get_for_job(spec.job_id, spec.organization_id)
            if existing is not None:
                self._validate_recovery(existing, revision, plan.manifest.checksum)
                records = await partitions.list_for_job(spec.job_id, spec.organization_id)
                if len(records) != len(plan.partitions):
                    if records:
                        raise RuntimeError("persisted manifest has incomplete partition records")
                    records = await partitions.add_all(
                        self._partition_records(spec, existing.id, object_key, plan)
                    )
                if existing.state == "building":
                    existing.object_key = object_key
                    existing.file_count = len(plan.manifest.entries)
                    existing.total_weight = plan.manifest.total_bytes
                    existing.partition_count = len(plan.partitions)
                    await manifests.transition(existing, "ready")
                await self._mark_parent_extracting(session, spec, existing, plan)
                return tuple(
                    PersistedPartition(record.id, existing.id, spec.job_id)
                    for record in records
                    if record.file_count > 0
                )

            manifest_id = _stable_id(
                "manifest",
                spec.organization_id,
                spec.job_id,
                revision,
                plan.manifest.checksum,
            )
            manifest = await manifests.add(
                ConnectorIngestionManifest(
                    id=manifest_id,
                    job_id=spec.job_id,
                    organization_id=spec.organization_id,
                    resolved_revision=revision,
                    checksum=plan.manifest.checksum,
                    object_key=object_key,
                    state="building",
                    file_count=len(plan.manifest.entries),
                    total_weight=plan.manifest.total_bytes,
                    partition_count=len(plan.partitions),
                    metadata_json={
                        "format": MANIFEST_FORMAT,
                        "checksum_algorithm": "sha256",
                    },
                )
            )
            records = self._partition_records(spec, manifest.id, object_key, plan)
            await partitions.add_all(records)
            await manifests.transition(manifest, "ready")
            await self._mark_parent_extracting(session, spec, manifest, plan)
            return tuple(
                PersistedPartition(record.id, manifest.id, spec.job_id)
                for record in records
                if record.file_count > 0
            )

    @staticmethod
    async def _mark_parent_extracting(
        session: AsyncSession,
        spec: GitJobSpec,
        manifest: ConnectorIngestionManifest,
        plan: IngestionPlan,
    ) -> None:
        """Expose the durable fan-out boundary on the parent job."""
        job = await session.get(ConnectorIngestionJob, spec.job_id)
        if job is None or job.organization_id != spec.organization_id:
            raise RuntimeError("parent ingestion job disappeared")
        job.state = job.stage = "extracting"
        job.files_discovered = len(plan.manifest.entries)
        job.progress_percent = max(job.progress_percent, 15)
        job.checkpoint = {
            **(job.checkpoint or {}),
            "manifest_id": manifest.id,
            "manifest_checksum": manifest.checksum,
            "manifest_object_key": manifest.object_key,
            "partition_count": len(plan.partitions),
        }

    @staticmethod
    def _partition_records(
        spec: GitJobSpec,
        manifest_id: str,
        object_key: str,
        plan: IngestionPlan,
    ) -> list[ConnectorIngestionPartition]:
        """Map pure deterministic partitions to durable records."""
        return [
            ConnectorIngestionPartition(
                id=_stable_id("partition", manifest_id, str(partition.index)),
                manifest_id=manifest_id,
                job_id=spec.job_id,
                organization_id=spec.organization_id,
                partition_number=partition.index,
                state="pending" if partition.entries else "committed",
                file_count=len(partition.entries),
                estimated_weight=partition.total_weight,
                checkpoint={
                    "partition_checksum": partition.checksum,
                    "manifest_object_key": object_key,
                },
            )
            for partition in plan.partitions
        ]

    @staticmethod
    def _validate_recovery(
        manifest: ConnectorIngestionManifest,
        revision: str,
        checksum: str,
    ) -> None:
        if manifest.resolved_revision != revision or manifest.checksum != checksum:
            raise RuntimeError("coordinator recovery resolved a different immutable manifest")
        if manifest.state in {"failed", "cancelled"}:
            raise RuntimeError(f"cannot recover terminal {manifest.state} manifest")


class ConnectorIngestionCoordinator:
    """Acquire once, publish an immutable plan, then fan out partition IDs."""

    def __init__(
        self,
        *,
        jobs: JobStore,
        plans: CoordinatorPlanStore,
        publisher: PartitionPublisher,
        object_store: ObjectStore,
        workspace: GitWorkspace,
        workspace_root: Path,
        scan_limits: ScanLimits,
        partition_count: int,
    ) -> None:
        """Compose lifecycle, storage, Git, and queue boundaries."""
        if partition_count < 1:
            raise ValueError("partition_count must be positive")
        self._jobs = jobs
        self._plans = plans
        self._publisher = publisher
        self._object_store = object_store
        self._workspace = workspace
        self._workspace_root = workspace_root
        self._scan_limits = scan_limits
        self._partition_count = partition_count

    async def coordinate(self, *, job_id: str, organization_id: str) -> CoordinationResult | None:
        """Coordinate one claimed parent job, safely replaying after a crash."""
        spec = await self._jobs.claim(job_id, organization_id)
        if spec is None:
            return None
        cancel = asyncio.Event()
        cancellation_poll = asyncio.create_task(self._poll_cancellation(spec.job_id, cancel))
        try:
            await self._jobs.mark_stage(spec.job_id, "cloning")
            repository = await self._workspace.prepare(
                repo_url=spec.repo_url,
                branch=spec.branch,
                destination=self._repository_path(spec),
                cancel=cancel,
                access_token=spec.access_token,
            )
            revision = (
                await self._workspace.checkout_revision(
                    repository,
                    spec.requested_revision,
                    cancel=cancel,
                    access_token=spec.access_token,
                )
                if spec.requested_revision
                else await self._workspace.current_revision(repository, cancel=cancel)
            )
            if spec.resolved_revision and revision != spec.resolved_revision:
                raise RuntimeError("source revision changed during coordinator recovery")
            await self._jobs.record_revision(spec.job_id, revision)
            spec = replace(spec, resolved_revision=revision)
            if revision == spec.last_successful_revision:
                await self._jobs.complete(spec.job_id)
                return CoordinationResult("unchanged", revision)

            await self._jobs.mark_stage(spec.job_id, "scanning")
            plan = await plan_repository(
                repository,
                limits=self._scan_limits,
                partition_count=self._partition_count,
                cancel=cancel,
            )
            if not plan.manifest.entries:
                raise RuntimeError("repository produced an empty manifest")
            if cancel.is_set():
                raise IngestionCancelledError("manifest coordination cancelled")

            object_key = _manifest_object_key(spec, revision, plan)
            await store_manifest_plan(
                self._object_store,
                object_key=object_key,
                revision=revision,
                plan=plan,
            )
            if cancel.is_set():
                raise IngestionCancelledError("manifest coordination cancelled")
            durable = await self._plans.persist(
                spec,
                revision=revision,
                plan=plan,
                object_key=object_key,
            )
            # A crash in this loop is safe: replay republishes the same IDs and
            # partition leasing prevents two workers from owning the same work.
            for partition in durable:
                if cancel.is_set():
                    raise IngestionCancelledError("partition publication cancelled")
                await self._publisher.enqueue(
                    job_id=partition.job_id,
                    manifest_id=partition.manifest_id,
                    partition_id=partition.partition_id,
                )
            return CoordinationResult(
                status="partitioned",
                resolved_revision=revision,
                manifest_id=durable[0].manifest_id if durable else None,
                manifest_checksum=plan.manifest.checksum,
                partition_count=len(durable),
            )
        except IngestionCancelledError:
            await self._jobs.cancel(spec.job_id)
            return CoordinationResult("cancelled", spec.resolved_revision or "")
        except Exception as exc:
            await self._jobs.fail(
                spec.job_id,
                _safe_error(exc),
                retrying=True,
            )
            raise
        finally:
            cancellation_poll.cancel()
            await asyncio.gather(cancellation_poll, return_exceptions=True)

    def _repository_path(self, spec: GitJobSpec) -> Path:
        return repository_workspace_path(self._workspace_root, spec.organization_id, spec.job_id)

    async def _poll_cancellation(self, job_id: str, cancellation: asyncio.Event) -> None:
        while not cancellation.is_set():
            if not await self._jobs.renew_lease(job_id):
                cancellation.set()
                return
            if await self._jobs.cancellation_requested(job_id):
                cancellation.set()
                return
            await asyncio.sleep(2)


async def store_manifest_plan(
    object_store: ObjectStore,
    *,
    object_key: str,
    revision: str,
    plan: IngestionPlan,
) -> None:
    """Stream a compressed full manifest to durable object storage."""
    temporary_path = await asyncio.to_thread(_write_manifest_file, revision, plan)
    try:
        await object_store.put_file(
            object_key,
            temporary_path,
            content_type="application/gzip",
        )
    finally:
        await asyncio.to_thread(temporary_path.unlink, missing_ok=True)


async def iter_stored_manifest(
    object_store: ObjectStore, object_key: str
) -> AsyncIterator[dict[str, object]]:
    """Yield and validate stored manifest records without retaining all entries."""
    with tempfile.NamedTemporaryFile(
        prefix="ecms-manifest-read-", suffix=".jsonl.gz", delete=False
    ) as handle:
        temporary_path = Path(handle.name)
        async for chunk in object_store.iter_object(object_key):
            await asyncio.to_thread(handle.write, chunk)
    try:
        with gzip.open(temporary_path, "rt", encoding="utf-8") as stream:
            first = True
            while raw_line := await asyncio.to_thread(stream.readline):
                value = json.loads(raw_line)
                if not isinstance(value, dict):
                    raise ValueError("stored manifest contains a non-object record")
                if first:
                    if value.get("format") != MANIFEST_FORMAT:
                        raise ValueError("stored manifest format is unsupported")
                    first = False
                yield value
            if first:
                raise ValueError("stored manifest is empty")
    finally:
        await asyncio.to_thread(temporary_path.unlink, missing_ok=True)


def _write_manifest_file(revision: str, plan: IngestionPlan) -> Path:
    partition_by_entry = {
        entry.checksum: partition.index
        for partition in plan.partitions
        for entry in partition.entries
    }
    with tempfile.NamedTemporaryFile(
        prefix="ecms-manifest-", suffix=".jsonl.gz", delete=False
    ) as handle:
        path = Path(handle.name)
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as stream:
        header = {
            "format": MANIFEST_FORMAT,
            "revision": revision,
            "manifest_checksum": plan.manifest.checksum,
            "file_count": len(plan.manifest.entries),
            "total_bytes": plan.manifest.total_bytes,
            "partition_count": len(plan.partitions),
        }
        stream.write(json.dumps(header, sort_keys=True, separators=(",", ":")) + "\n")
        for entry in plan.manifest.entries:
            record = {
                **entry.as_dict(),
                "entry_checksum": entry.checksum,
                "partition_index": partition_by_entry[entry.checksum],
            }
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return path


def _manifest_object_key(spec: GitJobSpec, revision: str, plan: IngestionPlan) -> str:
    tenant = hashlib.sha256(spec.organization_id.encode()).hexdigest()[:20]
    return f"connector-ingestion/manifests/{tenant}/{revision}/{plan.manifest.checksum}.jsonl.gz"


def repository_workspace_path(root: Path, organization_id: str, job_id: str) -> Path:
    """Return the shared traversal-safe checkout path for a parent job."""
    org = hashlib.sha256(organization_id.encode()).hexdigest()[:20]
    job = hashlib.sha256(job_id.encode()).hexdigest()[:20]
    return root / org / job


def _stable_id(namespace: str, *values: str) -> str:
    digest = hashlib.sha256("\0".join((namespace, *values)).encode()).hexdigest()
    return f"{namespace[:8]}-{digest[:48]}"


def _safe_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"[:2_000]


def extraction_queue_publisher(queue: ExtractionQueue) -> PartitionPublisher:
    """Expose the concrete extraction queue through the coordinator port."""
    return queue
