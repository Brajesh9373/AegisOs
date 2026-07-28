"""Executable process for persistence-aware connector extraction workers."""

from __future__ import annotations

import asyncio
import logging
import os
import socket
from datetime import UTC, timedelta
from pathlib import Path

from redis.asyncio import Redis
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.configuration.schemas.settings import get_settings
from ecms.connectors.ingestion.coordinator_runtime import repository_workspace_path
from ecms.connectors.ingestion.extraction_runtime import (
    ExtractionHandler,
    PartitionWork,
    StagedBatch,
)
from ecms.connectors.ingestion.extraction_worker import ExtractionWorker
from ecms.connectors.ingestion.parallel_queue import (
    ExtractionDelivery,
    ExtractionQueue,
    GraphWriteQueue,
)
from ecms.infrastructure.storage.factory import create_snapshot_object_store
from ecms.persistence.database.rest_session import db_session
from ecms.persistence.models.connector_ingestion_job import ConnectorIngestionJob
from ecms.persistence.models.connector_ingestion_partition import (
    ConnectorIngestionManifest,
    ConnectorIngestionPartition,
    ConnectorIngestionStageBatch,
)
from ecms.shared.time import utcnow

logger = logging.getLogger(__name__)


class PostgresExtractionStore:
    """Persist extraction lifecycle in small independently committed transactions."""

    def __init__(
        self,
        *,
        workspace: Path,
        lease_seconds: int,
        max_staged_bytes_per_org: int,
    ) -> None:
        """Configure workspace, lease duration, and durable backpressure."""
        self._workspace = workspace
        self._lease_seconds = lease_seconds
        self._max_staged_bytes_per_org = max_staged_bytes_per_org

    async def load_claimed(
        self, delivery: ExtractionDelivery, worker_id: str
    ) -> PartitionWork | None:
        """Atomically claim a delivered partition or resume this process's lease."""
        async with db_session() as session:
            partition = await session.scalar(
                select(ConnectorIngestionPartition)
                .where(
                    ConnectorIngestionPartition.id == delivery.partition_id,
                    ConnectorIngestionPartition.job_id == delivery.job_id,
                    ConnectorIngestionPartition.manifest_id == delivery.manifest_id,
                )
                .with_for_update()
            )
            if partition is None:
                return None
            now = utcnow()
            lease_expiry = partition.lease_expires_at
            if lease_expiry is not None and lease_expiry.tzinfo is None:
                lease_expiry = lease_expiry.replace(tzinfo=UTC)
            owned = partition.lease_owner == worker_id and partition.state in {
                "claimed",
                "extracting",
            }
            claimable = partition.state in {"pending", "retry"} or (
                partition.state in {"claimed", "extracting"}
                and lease_expiry is not None
                and lease_expiry <= now
            )
            if not owned and not claimable:
                return None
            if not owned:
                partition.state = "claimed"
                partition.lease_owner = worker_id
                partition.attempt += 1
                partition.started_at = partition.started_at or now
            partition.lease_expires_at = now + timedelta(seconds=self._lease_seconds)
            manifest = await session.get(
                ConnectorIngestionManifest, partition.manifest_id
            )
            if (
                manifest is None
                or manifest.state != "ready"
                or not manifest.object_key
                or partition.partition_number >= manifest.partition_count
            ):
                raise ValueError("partition manifest is not ready")
            job = await session.get(ConnectorIngestionJob, partition.job_id)
            if job is None or job.organization_id != partition.organization_id:
                raise ValueError("partition parent job is unavailable")
            checkpoint = partition.checkpoint or {}
            repository = repository_workspace_path(
                self._workspace, partition.organization_id, partition.job_id
            )
            return PartitionWork(
                id=partition.id,
                job_id=partition.job_id,
                organization_id=partition.organization_id,
                connection_id=job.connection_id,
                manifest_id=manifest.id,
                manifest_object_key=manifest.object_key,
                manifest_checksum=manifest.checksum,
                resolved_revision=manifest.resolved_revision,
                partition_number=partition.partition_number,
                partition_count=manifest.partition_count,
                partition_checksum=checkpoint.get("partition_checksum"),
                repository=repository,
                next_sequence=int(checkpoint.get("next_sequence", 0)),
                files_processed=partition.files_processed,
                nodes_extracted=partition.nodes_extracted,
                edges_extracted=partition.edges_extracted,
            )

    async def begin(self, work: PartitionWork, worker_id: str) -> None:
        """Move a claimed partition into extraction."""
        async with db_session() as session:
            partition = await _owned_partition(session, work.id, worker_id)
            if partition.state == "claimed":
                partition.state = "extracting"

    async def renew(self, work: PartitionWork, worker_id: str) -> bool:
        """Renew the partition lease while ownership remains valid."""
        async with db_session() as session:
            partition = await session.get(ConnectorIngestionPartition, work.id)
            if (
                partition is None
                or partition.lease_owner != worker_id
                or partition.state not in {"claimed", "extracting"}
            ):
                return False
            partition.lease_expires_at = utcnow() + timedelta(
                seconds=self._lease_seconds
            )
            return True

    async def cancellation_requested(self, work: PartitionWork) -> bool:
        """Read parent-job cancellation state."""
        async with db_session() as session:
            state = await session.scalar(
                select(ConnectorIngestionJob.state).where(
                    ConnectorIngestionJob.id == work.job_id,
                    ConnectorIngestionJob.organization_id == work.organization_id,
                )
            )
            return state in {"cancel_requested", "cancelled"}

    async def register_batch(
        self, work: PartitionWork, batch: StagedBatch, worker_id: str
    ) -> bool:
        """Persist immutable batch metadata idempotently."""
        async with db_session() as session:
            await _owned_partition(session, work.id, worker_id)
            if session.bind is not None and session.bind.dialect.name == "postgresql":
                await session.execute(
                    text(
                        "SELECT pg_advisory_xact_lock("
                        "hashtextextended(:quota_key, 0))"
                    ),
                    {"quota_key": f"connector-staged:{work.organization_id}"},
                )
            existing = await session.scalar(
                select(ConnectorIngestionStageBatch).where(
                    ConnectorIngestionStageBatch.partition_id == work.id,
                    ConnectorIngestionStageBatch.sequence_number
                    == batch.sequence_number,
                )
            )
            if existing is not None:
                if (
                    existing.checksum != batch.checksum
                    or existing.object_key != batch.object_key
                ):
                    raise ValueError("staged sequence conflicts with immutable batch")
                return False
            staged_bytes = int(
                await session.scalar(
                    select(func.coalesce(func.sum(ConnectorIngestionStageBatch.byte_count), 0))
                    .where(
                        ConnectorIngestionStageBatch.organization_id
                        == work.organization_id,
                        ConnectorIngestionStageBatch.state.in_(("staged", "writing")),
                    )
                )
                or 0
            )
            if staged_bytes + len(batch.payload) > self._max_staged_bytes_per_org:
                raise RuntimeError("organization staged-byte limit reached")
            session.add(
                ConnectorIngestionStageBatch(
                    id=batch.id,
                    partition_id=work.id,
                    job_id=work.job_id,
                    organization_id=work.organization_id,
                    sequence_number=batch.sequence_number,
                    checksum=batch.checksum,
                    object_key=batch.object_key,
                    state="staged",
                    node_count=batch.node_count,
                    edge_count=batch.edge_count,
                    byte_count=len(batch.payload),
                )
            )
            return True

    async def checkpoint(
        self,
        work: PartitionWork,
        *,
        files_processed: int,
        nodes_extracted: int,
        edges_extracted: int,
        next_sequence: int,
        worker_id: str,
    ) -> None:
        """Persist a completed durable batch boundary."""
        async with db_session() as session:
            partition = await _owned_partition(session, work.id, worker_id)
            partition.files_processed = files_processed
            partition.nodes_extracted = nodes_extracted
            partition.edges_extracted = edges_extracted
            partition.checkpoint = {
                **(partition.checkpoint or {}),
                "next_sequence": next_sequence,
            }

    async def staged(self, work: PartitionWork, worker_id: str) -> None:
        """Mark extraction complete without writing to FalkorDB."""
        async with db_session() as session:
            partition = await _owned_partition(session, work.id, worker_id)
            partition.state = "staged"

    async def failed_attempt(
        self, work: PartitionWork, worker_id: str, error: Exception
    ) -> None:
        """Release a failed lease for bounded redelivery without exposing secrets."""
        async with db_session() as session:
            partition = await session.get(ConnectorIngestionPartition, work.id)
            if partition is None or partition.lease_owner != worker_id:
                return
            partition.state = "retry"
            partition.lease_owner = None
            partition.lease_expires_at = None
            partition.error_summary = f"{type(error).__name__}: {error}"[:2_000]

    async def exhausted(
        self, delivery: ExtractionDelivery, error: Exception
    ) -> None:
        """Make exhaustion and parent failure durable before stream acknowledgement."""
        async with db_session() as session:
            partition = await session.get(
                ConnectorIngestionPartition, delivery.partition_id
            )
            if (
                partition is None
                or partition.job_id != delivery.job_id
                or partition.manifest_id != delivery.manifest_id
            ):
                return
            safe_error = f"{type(error).__name__}: {error}"[:2_000]
            partition.state = "failed"
            partition.lease_owner = None
            partition.lease_expires_at = None
            partition.error_summary = safe_error
            partition.completed_at = utcnow()
            job = await session.get(ConnectorIngestionJob, delivery.job_id)
            if job is not None and job.organization_id == partition.organization_id:
                job.state = job.stage = "failed"
                job.error_code = "CONNECTOR_EXTRACTION_EXHAUSTED"
                job.error_summary = safe_error
                job.completed_at = utcnow()
                job.lease_owner = None
                job.lease_expires_at = None
                await session.execute(
                    text(
                        "UPDATE connections SET current_ingestion_job_id = :job_id, "
                        "sync_state = 'failed', last_error_summary = :error "
                        "WHERE number = :connection_id"
                    ),
                    {
                        "job_id": job.id,
                        "error": safe_error,
                        "connection_id": job.connection_id,
                    },
                )


async def _owned_partition(
    session: AsyncSession, partition_id: str, worker_id: str
) -> ConnectorIngestionPartition:
    partition = await session.get(ConnectorIngestionPartition, partition_id)
    if partition is None or partition.lease_owner != worker_id:
        raise ValueError("partition lease is not owned by this worker")
    return partition


async def run() -> None:
    """Run one extraction consumer per configured process."""
    settings = get_settings()
    if not settings.connector_parallel_ingestion_enabled:
        raise RuntimeError("parallel connector ingestion is disabled")
    worker_id = f"{socket.gethostname()}-{os.getpid()}"
    redis = Redis.from_url(settings.redis_url)
    extraction_queue = ExtractionQueue(redis, consumer=worker_id)
    graph_queue = GraphWriteQueue(redis, consumer=worker_id)
    await extraction_queue.ensure_group()
    await graph_queue.ensure_group()
    objects = create_snapshot_object_store(settings)
    await objects.ensure_bucket()
    store = PostgresExtractionStore(
        workspace=Path(settings.connector_ingestion_workspace),
        lease_seconds=settings.connector_ingestion_stale_after_seconds,
        max_staged_bytes_per_org=(
            settings.connector_ingestion_max_staged_bytes_per_org
        ),
    )
    worker = ExtractionWorker(
        extraction_queue,
        ExtractionHandler(
            store=store,
            objects=objects,
            graph_queue=graph_queue,
            worker_id=worker_id,
            chunk_size=settings.connector_ingestion_chunk_size,
            max_batch_encoded_bytes=(
                settings.connector_ingestion_max_batch_encoded_bytes
            ),
        ),
        max_deliveries=settings.connector_ingestion_max_deliveries,
        stale_after_ms=settings.connector_ingestion_stale_after_seconds * 1_000,
        on_exhausted=store.exhausted,
    )
    try:
        while True:
            await redis.set(
                f"ecms:connector-ingestion:extractor-health:{worker_id}",
                "1",
                ex=45,
            )
            result = await worker.process_one()
            if result.processed and result.outcome is not None:
                logger.warning(
                    "partition extraction delivery did not complete",
                    extra={"outcome": result.outcome},
                )
    finally:
        await redis.aclose()


def main() -> None:
    """Start a dedicated extraction worker process."""
    logging.basicConfig(level=os.environ.get("ECMS_LOG_LEVEL", "INFO"))
    asyncio.run(run())


if __name__ == "__main__":
    main()
