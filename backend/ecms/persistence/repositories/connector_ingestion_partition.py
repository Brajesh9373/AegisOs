"""Repositories and state invariants for partitioned connector ingestion."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.persistence.models.connector_ingestion_partition import (
    ConnectorIngestionManifest,
    ConnectorIngestionPartition,
    ConnectorIngestionStageBatch,
)
from ecms.shared.time import utcnow

MANIFEST_TRANSITIONS = {
    "building": frozenset({"ready", "failed", "cancelled"}),
    "ready": frozenset(),
    "failed": frozenset(),
    "cancelled": frozenset(),
}
PARTITION_TRANSITIONS = {
    "pending": frozenset({"claimed", "cancelled", "superseded"}),
    "claimed": frozenset({"extracting", "retry", "failed", "cancelled"}),
    "extracting": frozenset({"staged", "retry", "failed", "cancelled"}),
    "staged": frozenset({"committed", "retry", "failed", "cancelled"}),
    "retry": frozenset({"claimed", "cancelled", "superseded"}),
    "committed": frozenset(),
    "failed": frozenset({"retry", "superseded"}),
    "cancelled": frozenset(),
    "superseded": frozenset(),
}
STAGE_BATCH_TRANSITIONS = {
    "staged": frozenset({"writing", "failed", "cancelled"}),
    "writing": frozenset({"committed", "staged", "failed", "cancelled"}),
    "committed": frozenset(),
    "failed": frozenset({"staged"}),
    "cancelled": frozenset(),
}

__all__ = [
    "MANIFEST_TRANSITIONS",
    "PARTITION_TRANSITIONS",
    "STAGE_BATCH_TRANSITIONS",
    "ConnectorIngestionManifestRepository",
    "ConnectorIngestionPartitionRepository",
    "ConnectorIngestionStageBatchRepository",
]


def _transition(current: str, target: str, transitions: dict[str, frozenset[str]]) -> None:
    if target not in transitions.get(current, frozenset()):
        raise ValueError(f"illegal state transition: {current} -> {target}")


def _lease_expired(expires_at: datetime | None, now: datetime | None = None) -> bool:
    """Compare database timestamps safely across SQLite and PostgreSQL."""
    if expires_at is None:
        return True
    comparable_expiry = expires_at.replace(tzinfo=UTC) if expires_at.tzinfo is None else expires_at
    comparable_now = now or utcnow()
    if comparable_now.tzinfo is None:
        comparable_now = comparable_now.replace(tzinfo=UTC)
    return comparable_expiry < comparable_now


class ConnectorIngestionManifestRepository:
    """Persist immutable manifests and their publication readiness."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a transaction-scoped session."""
        self._session = session

    async def add(self, manifest: ConnectorIngestionManifest) -> ConnectorIngestionManifest:
        """Persist one manifest, allocating uniqueness constraints immediately."""
        self._session.add(manifest)
        await self._session.flush()
        return manifest

    async def get_for_job(
        self, job_id: str, organization_id: str
    ) -> ConnectorIngestionManifest | None:
        """Return the tenant-scoped manifest for a parent job."""
        result = await self._session.execute(
            select(ConnectorIngestionManifest).where(
                ConnectorIngestionManifest.job_id == job_id,
                ConnectorIngestionManifest.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get(
        self, manifest_id: str, organization_id: str
    ) -> ConnectorIngestionManifest | None:
        """Return a manifest only within the requesting organization."""
        result = await self._session.execute(
            select(ConnectorIngestionManifest).where(
                ConnectorIngestionManifest.id == manifest_id,
                ConnectorIngestionManifest.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def transition(
        self,
        manifest: ConnectorIngestionManifest,
        target: str,
        *,
        error_summary: str | None = None,
        now: datetime | None = None,
    ) -> ConnectorIngestionManifest:
        """Apply a legal manifest state transition."""
        _transition(manifest.state, target, MANIFEST_TRANSITIONS)
        manifest.state = target
        manifest.error_summary = error_summary[:4_000] if error_summary else None
        if target in {"ready", "failed", "cancelled"}:
            manifest.completed_at = now or utcnow()
        await self._session.flush()
        return manifest


class ConnectorIngestionPartitionRepository:
    """Create, exclusively lease, and aggregate deterministic partitions."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a transaction-scoped session."""
        self._session = session

    async def add_all(
        self, partitions: list[ConnectorIngestionPartition]
    ) -> list[ConnectorIngestionPartition]:
        """Persist a deterministic set of manifest partitions."""
        self._session.add_all(partitions)
        await self._session.flush()
        return partitions

    async def list_for_job(
        self, job_id: str, organization_id: str
    ) -> list[ConnectorIngestionPartition]:
        """List a tenant-scoped job's partitions in deterministic order."""
        result = await self._session.execute(
            select(ConnectorIngestionPartition)
            .where(
                ConnectorIngestionPartition.job_id == job_id,
                ConnectorIngestionPartition.organization_id == organization_id,
            )
            .order_by(ConnectorIngestionPartition.partition_number)
            .execution_options(populate_existing=True)
        )
        return list(result.scalars())

    async def get(
        self, partition_id: str, organization_id: str
    ) -> ConnectorIngestionPartition | None:
        """Return a partition only within the requesting organization."""
        result = await self._session.execute(
            select(ConnectorIngestionPartition).where(
                ConnectorIngestionPartition.id == partition_id,
                ConnectorIngestionPartition.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def claim_next(
        self,
        *,
        job_id: str,
        organization_id: str,
        worker_id: str,
        lease_seconds: int,
        now: datetime | None = None,
    ) -> ConnectorIngestionPartition | None:
        """Atomically claim one pending/retry or expired claimed partition."""
        claimed_at = now or utcnow()
        candidate = (
            await self._session.execute(
                select(ConnectorIngestionPartition.id)
                .where(
                    ConnectorIngestionPartition.job_id == job_id,
                    ConnectorIngestionPartition.organization_id == organization_id,
                    or_(
                        ConnectorIngestionPartition.state.in_(("pending", "retry")),
                        (
                            (ConnectorIngestionPartition.state == "claimed")
                            & (ConnectorIngestionPartition.lease_expires_at < claimed_at)
                        ),
                    ),
                )
                .order_by(
                    ConnectorIngestionPartition.estimated_weight.desc(),
                    ConnectorIngestionPartition.partition_number,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if candidate is None:
            return None
        result = await self._session.execute(
            update(ConnectorIngestionPartition)
            .where(
                ConnectorIngestionPartition.id == candidate,
                or_(
                    ConnectorIngestionPartition.state.in_(("pending", "retry")),
                    (
                        (ConnectorIngestionPartition.state == "claimed")
                        & (ConnectorIngestionPartition.lease_expires_at < claimed_at)
                    ),
                ),
            )
            .values(
                state="claimed",
                lease_owner=worker_id,
                lease_expires_at=claimed_at + timedelta(seconds=max(lease_seconds, 1)),
                started_at=func.coalesce(ConnectorIngestionPartition.started_at, claimed_at),
                attempt=ConnectorIngestionPartition.attempt + 1,
                error_summary=None,
            )
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            return None
        partition = await self._session.get(ConnectorIngestionPartition, candidate)
        if partition is not None:
            await self._session.refresh(partition)
        return partition

    async def renew_lease(
        self,
        partition_id: str,
        *,
        organization_id: str,
        worker_id: str,
        lease_seconds: int,
        now: datetime | None = None,
    ) -> bool:
        """Renew a live extraction lease only for its current owner."""
        renewed_at = now or utcnow()
        result = await self._session.execute(
            update(ConnectorIngestionPartition)
            .where(
                ConnectorIngestionPartition.id == partition_id,
                ConnectorIngestionPartition.organization_id == organization_id,
                ConnectorIngestionPartition.lease_owner == worker_id,
                ConnectorIngestionPartition.state.in_(("claimed", "extracting")),
                ConnectorIngestionPartition.lease_expires_at >= renewed_at,
            )
            .values(lease_expires_at=renewed_at + timedelta(seconds=max(lease_seconds, 1)))
            .execution_options(synchronize_session=False)
        )
        return result.rowcount == 1

    async def update_checkpoint(
        self,
        partition: ConnectorIngestionPartition,
        *,
        worker_id: str,
        checkpoint: dict[str, object],
        files_processed: int | None = None,
        nodes_extracted: int | None = None,
        edges_extracted: int | None = None,
    ) -> ConnectorIngestionPartition:
        """Durably checkpoint extraction progress under the active lease."""
        if partition.lease_owner != worker_id:
            raise ValueError("partition lease is not owned by this worker")
        if _lease_expired(partition.lease_expires_at):
            raise ValueError("partition lease has expired")
        if partition.state not in {"claimed", "extracting"}:
            raise ValueError("partition must be claimed or extracting to checkpoint")
        partition.checkpoint = {**partition.checkpoint, **checkpoint}
        if files_processed is not None:
            partition.files_processed = max(files_processed, partition.files_processed)
        if nodes_extracted is not None:
            partition.nodes_extracted = max(nodes_extracted, partition.nodes_extracted)
        if edges_extracted is not None:
            partition.edges_extracted = max(edges_extracted, partition.edges_extracted)
        await self._session.flush()
        return partition

    async def transition(
        self,
        partition: ConnectorIngestionPartition,
        target: str,
        *,
        worker_id: str | None = None,
        error_summary: str | None = None,
        now: datetime | None = None,
    ) -> ConnectorIngestionPartition:
        """Apply a legal transition, optionally enforcing lease ownership."""
        _transition(partition.state, target, PARTITION_TRANSITIONS)
        if worker_id is not None and partition.lease_owner != worker_id:
            raise ValueError("partition lease is not owned by this worker")
        if worker_id is not None and _lease_expired(partition.lease_expires_at, now):
            raise ValueError("partition lease has expired")
        partition.state = target
        partition.error_summary = error_summary[:4_000] if error_summary else None
        if target in {"retry", "committed", "failed", "cancelled", "superseded"}:
            partition.lease_owner = None
            partition.lease_expires_at = None
        if target in {"committed", "failed", "cancelled", "superseded"}:
            partition.completed_at = now or utcnow()
        await self._session.flush()
        return partition

    async def state_counts(self, job_id: str, organization_id: str) -> dict[str, int]:
        """Aggregate partition lifecycle counts for parent progress."""
        result = await self._session.execute(
            select(ConnectorIngestionPartition.state, func.count())
            .where(
                ConnectorIngestionPartition.job_id == job_id,
                ConnectorIngestionPartition.organization_id == organization_id,
            )
            .group_by(ConnectorIngestionPartition.state)
        )
        return dict(result.all())

    async def reconcile(self, job_id: str, organization_id: str) -> dict[str, object]:
        """Return authoritative fan-in totals derived from durable child rows."""
        rows = (
            await self._session.execute(
                select(
                    ConnectorIngestionPartition.state,
                    func.count(),
                    func.coalesce(func.sum(ConnectorIngestionPartition.file_count), 0),
                    func.coalesce(func.sum(ConnectorIngestionPartition.files_processed), 0),
                    func.coalesce(func.sum(ConnectorIngestionPartition.nodes_extracted), 0),
                    func.coalesce(func.sum(ConnectorIngestionPartition.edges_extracted), 0),
                )
                .where(
                    ConnectorIngestionPartition.job_id == job_id,
                    ConnectorIngestionPartition.organization_id == organization_id,
                )
                .group_by(ConnectorIngestionPartition.state)
            )
        ).all()
        states = {state: count for state, count, *_ in rows}
        return {
            "states": states,
            "partition_count": sum(states.values()),
            "file_count": sum(row[2] for row in rows),
            "files_processed": sum(row[3] for row in rows),
            "nodes_extracted": sum(row[4] for row in rows),
            "edges_extracted": sum(row[5] for row in rows),
            "all_committed": bool(states) and states.get("committed", 0) == sum(states.values()),
            "has_failures": states.get("failed", 0) > 0,
        }

    async def cancel_for_job(
        self,
        job_id: str,
        organization_id: str,
        *,
        now: datetime | None = None,
    ) -> int:
        """Cancel every non-terminal partition and release its lease."""
        result = await self._session.execute(
            update(ConnectorIngestionPartition)
            .where(
                ConnectorIngestionPartition.job_id == job_id,
                ConnectorIngestionPartition.organization_id == organization_id,
                ConnectorIngestionPartition.state.in_(
                    ("pending", "claimed", "extracting", "staged", "retry")
                ),
            )
            .values(
                state="cancelled",
                lease_owner=None,
                lease_expires_at=None,
                completed_at=now or utcnow(),
            )
            .execution_options(synchronize_session=False)
        )
        return result.rowcount


class ConnectorIngestionStageBatchRepository:
    """Persist and exclusively lease immutable graph-write batches."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a transaction-scoped session."""
        self._session = session

    async def add(self, batch: ConnectorIngestionStageBatch) -> ConnectorIngestionStageBatch:
        """Persist a checksummed immutable staged batch."""
        self._session.add(batch)
        await self._session.flush()
        return batch

    async def get_by_checksum(
        self, partition_id: str, checksum: str
    ) -> ConnectorIngestionStageBatch | None:
        """Resolve an existing staged batch for idempotent producer retries."""
        result = await self._session.execute(
            select(ConnectorIngestionStageBatch).where(
                ConnectorIngestionStageBatch.partition_id == partition_id,
                ConnectorIngestionStageBatch.checksum == checksum,
            )
        )
        return result.scalar_one_or_none()

    async def get(self, batch_id: str, organization_id: str) -> ConnectorIngestionStageBatch | None:
        """Return a staged batch only within the requesting organization."""
        result = await self._session.execute(
            select(ConnectorIngestionStageBatch).where(
                ConnectorIngestionStageBatch.id == batch_id,
                ConnectorIngestionStageBatch.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_job(
        self, job_id: str, organization_id: str
    ) -> list[ConnectorIngestionStageBatch]:
        """List all tenant-scoped batches in deterministic write order."""
        result = await self._session.execute(
            select(ConnectorIngestionStageBatch)
            .where(
                ConnectorIngestionStageBatch.job_id == job_id,
                ConnectorIngestionStageBatch.organization_id == organization_id,
            )
            .order_by(
                ConnectorIngestionStageBatch.partition_id,
                ConnectorIngestionStageBatch.sequence_number,
            )
            .execution_options(populate_existing=True)
        )
        return list(result.scalars())

    async def claim_next(
        self,
        *,
        job_id: str,
        organization_id: str,
        writer_id: str,
        lease_seconds: int,
        now: datetime | None = None,
    ) -> ConnectorIngestionStageBatch | None:
        """Atomically claim a staged or expired writing batch."""
        claimed_at = now or utcnow()
        eligible = or_(
            ConnectorIngestionStageBatch.state == "staged",
            (
                (ConnectorIngestionStageBatch.state == "writing")
                & (ConnectorIngestionStageBatch.writer_lease_expires_at < claimed_at)
            ),
        )
        candidate = (
            await self._session.execute(
                select(ConnectorIngestionStageBatch.id)
                .where(
                    ConnectorIngestionStageBatch.job_id == job_id,
                    ConnectorIngestionStageBatch.organization_id == organization_id,
                    eligible,
                )
                .order_by(
                    ConnectorIngestionStageBatch.partition_id,
                    ConnectorIngestionStageBatch.sequence_number,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        if candidate is None:
            return None
        result = await self._session.execute(
            update(ConnectorIngestionStageBatch)
            .where(ConnectorIngestionStageBatch.id == candidate, eligible)
            .values(
                state="writing",
                writer_owner=writer_id,
                writer_lease_expires_at=claimed_at + timedelta(seconds=max(lease_seconds, 1)),
                attempt=ConnectorIngestionStageBatch.attempt + 1,
                error_summary=None,
            )
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            return None
        batch = await self._session.get(ConnectorIngestionStageBatch, candidate)
        if batch is not None:
            await self._session.refresh(batch)
        return batch

    async def renew_lease(
        self,
        batch_id: str,
        *,
        organization_id: str,
        writer_id: str,
        lease_seconds: int,
        now: datetime | None = None,
    ) -> bool:
        """Renew a live graph-write lease only for its current owner."""
        renewed_at = now or utcnow()
        result = await self._session.execute(
            update(ConnectorIngestionStageBatch)
            .where(
                ConnectorIngestionStageBatch.id == batch_id,
                ConnectorIngestionStageBatch.organization_id == organization_id,
                ConnectorIngestionStageBatch.writer_owner == writer_id,
                ConnectorIngestionStageBatch.state == "writing",
                ConnectorIngestionStageBatch.writer_lease_expires_at >= renewed_at,
            )
            .values(writer_lease_expires_at=renewed_at + timedelta(seconds=max(lease_seconds, 1)))
            .execution_options(synchronize_session=False)
        )
        return result.rowcount == 1

    async def transition(
        self,
        batch: ConnectorIngestionStageBatch,
        target: str,
        *,
        writer_id: str | None = None,
        lease_seconds: int = 60,
        error_summary: str | None = None,
        now: datetime | None = None,
    ) -> ConnectorIngestionStageBatch:
        """Apply a legal graph-write lifecycle transition."""
        if target == "writing" and writer_id is None:
            raise ValueError("writer_id is required to write a stage batch")
        if writer_id is not None and batch.writer_owner not in {None, writer_id}:
            raise ValueError("stage batch lease is owned by another writer")
        if (
            writer_id is not None
            and batch.writer_owner == writer_id
            and _lease_expired(batch.writer_lease_expires_at, now)
        ):
            raise ValueError("stage batch lease has expired")
        _transition(batch.state, target, STAGE_BATCH_TRANSITIONS)
        changed_at = now or utcnow()
        batch.state = target
        batch.error_summary = error_summary[:4_000] if error_summary else None
        if target == "writing":
            batch.writer_owner = writer_id
            batch.writer_lease_expires_at = changed_at + timedelta(seconds=max(lease_seconds, 1))
            batch.attempt += 1
        if target in {"staged", "committed", "failed", "cancelled"}:
            batch.writer_owner = None
            batch.writer_lease_expires_at = None
        if target == "committed":
            batch.committed_at = changed_at
        await self._session.flush()
        return batch

    async def reconcile(self, job_id: str, organization_id: str) -> dict[str, object]:
        """Return authoritative staged-write totals for fan-in."""
        rows = (
            await self._session.execute(
                select(
                    ConnectorIngestionStageBatch.state,
                    func.count(),
                    func.coalesce(func.sum(ConnectorIngestionStageBatch.node_count), 0),
                    func.coalesce(func.sum(ConnectorIngestionStageBatch.edge_count), 0),
                    func.coalesce(func.sum(ConnectorIngestionStageBatch.byte_count), 0),
                )
                .where(
                    ConnectorIngestionStageBatch.job_id == job_id,
                    ConnectorIngestionStageBatch.organization_id == organization_id,
                )
                .group_by(ConnectorIngestionStageBatch.state)
            )
        ).all()
        states = {state: count for state, count, *_ in rows}
        return {
            "states": states,
            "batch_count": sum(states.values()),
            "node_count": sum(row[2] for row in rows),
            "edge_count": sum(row[3] for row in rows),
            "byte_count": sum(row[4] for row in rows),
            "all_committed": bool(states) and states.get("committed", 0) == sum(states.values()),
            "has_failures": states.get("failed", 0) > 0,
        }

    async def cancel_for_job(
        self,
        job_id: str,
        organization_id: str,
    ) -> int:
        """Cancel every uncommitted batch and release writer leases."""
        result = await self._session.execute(
            update(ConnectorIngestionStageBatch)
            .where(
                ConnectorIngestionStageBatch.job_id == job_id,
                ConnectorIngestionStageBatch.organization_id == organization_id,
                ConnectorIngestionStageBatch.state.in_(("staged", "writing", "failed")),
            )
            .values(
                state="cancelled",
                writer_owner=None,
                writer_lease_expires_at=None,
            )
            .execution_options(synchronize_session=False)
        )
        return result.rowcount
