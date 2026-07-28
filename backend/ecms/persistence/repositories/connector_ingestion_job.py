"""Persistence operations for durable connector ingestion jobs."""

from __future__ import annotations

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.persistence.models.connector_ingestion_job import ConnectorIngestionJob
from ecms.persistence.models.connector_ingestion_partition import (
    ConnectorIngestionManifest,
    ConnectorIngestionPartition,
    ConnectorIngestionStageBatch,
)
from ecms.shared.time import utcnow

ACTIVE_STATES = frozenset(
    {
        "queued",
        "validating",
        "cloning",
        "scanning",
        "extracting",
        "writing",
        "snapshotting",
        "cancel_requested",
        "retrying",
    }
)

__all__ = ["ACTIVE_STATES", "ConnectorIngestionJobRepository"]


class ConnectorIngestionJobRepository:
    """Tenant-safe job queries and connection synchronization updates."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a transaction-scoped session."""
        self._session = session

    async def get(self, job_id: str, organization_id: str) -> ConnectorIngestionJob | None:
        """Return a job only within the requesting organization."""
        result = await self._session.execute(
            select(ConnectorIngestionJob).where(
                ConnectorIngestionJob.id == job_id,
                ConnectorIngestionJob.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active(
        self,
        organization_id: str,
        repository_identity: str,
        branch: str,
    ) -> ConnectorIngestionJob | None:
        """Return the active job for a normalized repository and branch."""
        result = await self._session.execute(
            select(ConnectorIngestionJob)
            .where(
                ConnectorIngestionJob.organization_id == organization_id,
                ConnectorIngestionJob.repository_identity == repository_identity,
                ConnectorIngestionJob.branch == branch,
                ConnectorIngestionJob.state.in_(ACTIVE_STATES),
            )
            .order_by(ConnectorIngestionJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(
        self,
        organization_id: str,
        idempotency_key: str,
    ) -> ConnectorIngestionJob | None:
        """Find a prior request by its caller-provided idempotency key."""
        result = await self._session.execute(
            select(ConnectorIngestionJob)
            .where(
                ConnectorIngestionJob.organization_id == organization_id,
                ConnectorIngestionJob.idempotency_key == idempotency_key,
            )
            .order_by(ConnectorIngestionJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def add(self, job: ConnectorIngestionJob) -> ConnectorIngestionJob:
        """Persist a new job and allocate database constraints immediately."""
        self._session.add(job)
        await self._session.flush()
        return job

    async def owned_connection(
        self,
        connection_id: int,
        *,
        owner_email: str,
    ) -> dict[str, object] | None:
        """Resolve a non-deleted connection owned by the authenticated user."""
        row = (
            (
                await self._session.execute(
                    text(
                        "SELECT connections.* FROM connections "
                        "JOIN users ON users.id = connections.user_id "
                        "WHERE connections.number = :connection_id "
                        "AND lower(users.email) = lower(:owner_email) "
                        "AND connections.status != 'deleted'"
                    ),
                    {"connection_id": connection_id, "owner_email": owner_email},
                )
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    async def mark_connection_job(
        self,
        connection_id: int,
        *,
        organization_id: str,
        job_id: str,
        sync_state: str,
        error_summary: str | None = None,
    ) -> None:
        """Expose the current job lifecycle on the connection record."""
        await self._session.execute(
            text(
                "UPDATE connections SET organization_id = :organization_id, "
                "current_ingestion_job_id = :job_id, sync_state = :sync_state, "
                "last_error_summary = :error_summary WHERE number = :connection_id"
            ),
            {
                "connection_id": connection_id,
                "organization_id": organization_id,
                "job_id": job_id,
                "sync_state": sync_state,
                "error_summary": error_summary,
            },
        )

    async def cancel_job_tree(
        self,
        job_id: str,
        organization_id: str,
    ) -> ConnectorIngestionJob | None:
        """Atomically cancel a parent and every active durable child.

        The caller controls commit/rollback. Committed graph batches and
        partitions remain immutable, while all leases in the active tree are
        released. Connection state is changed only when it still points at this
        job, preventing an old cancellation from overwriting a newer attempt.
        """
        job = await self.get(job_id, organization_id)
        if job is None:
            return None
        if job.state in {"ready", "failed"}:
            raise ValueError("completed ingestion jobs cannot be cancelled")
        if job.state == "cancelled":
            return job

        cancelled_at = utcnow()
        await self._session.execute(
            update(ConnectorIngestionManifest)
            .where(
                ConnectorIngestionManifest.job_id == job_id,
                ConnectorIngestionManifest.organization_id == organization_id,
                ConnectorIngestionManifest.state == "building",
            )
            .values(
                state="cancelled",
                completed_at=cancelled_at,
                error_summary=None,
            )
            .execution_options(synchronize_session=False)
        )
        await self._session.execute(
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
                completed_at=cancelled_at,
                error_summary=None,
            )
            .execution_options(synchronize_session=False)
        )
        await self._session.execute(
            update(ConnectorIngestionStageBatch)
            .where(
                ConnectorIngestionStageBatch.job_id == job_id,
                ConnectorIngestionStageBatch.organization_id == organization_id,
                ConnectorIngestionStageBatch.state.in_(("staged", "writing")),
            )
            .values(
                state="cancelled",
                writer_owner=None,
                writer_lease_expires_at=None,
                error_summary=None,
            )
            .execution_options(synchronize_session=False)
        )
        job.state = "cancelled"
        job.stage = "cancelled"
        job.cancellation_requested = True
        job.lease_owner = None
        job.lease_expires_at = None
        job.error_code = None
        job.error_summary = None
        job.completed_at = cancelled_at
        job.updated_at = cancelled_at
        await self._session.execute(
            text(
                "UPDATE connections SET organization_id = :organization_id, "
                "sync_state = 'cancelled', "
                "last_error_summary = NULL "
                "WHERE number = :connection_id "
                "AND current_ingestion_job_id = :job_id "
                "AND (organization_id = :organization_id OR organization_id IS NULL)"
            ),
            {
                "connection_id": job.connection_id,
                "organization_id": organization_id,
                "job_id": job_id,
            },
        )
        await self._session.flush()
        return job
