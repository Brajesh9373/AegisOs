"""Executable parent coordinator for partitioned connector ingestion."""

from __future__ import annotations

import asyncio
import logging
import os
import socket
from pathlib import Path

from redis.asyncio import Redis

from ecms.configuration.schemas.settings import get_settings
from ecms.connectors.ingestion.coordinator_runtime import (
    ConnectorIngestionCoordinator,
    SqlCoordinatorPlanStore,
)
from ecms.connectors.ingestion.git_runtime import GitCommandRunner, GitLimits, GitWorkspace
from ecms.connectors.ingestion.parallel_queue import ExtractionQueue
from ecms.connectors.ingestion.queue import IngestionQueue
from ecms.connectors.ingestion.scanner import ScanLimits
from ecms.connectors.ingestion.worker import PostgresJobStore
from ecms.infrastructure.storage.factory import create_snapshot_object_store

logger = logging.getLogger(__name__)


async def run() -> None:
    """Consume parent jobs and fan out durable extraction partition IDs."""
    settings = get_settings()
    if not settings.connector_parallel_ingestion_enabled:
        raise RuntimeError("parallel connector ingestion is disabled")
    worker_id = f"{socket.gethostname()}-{os.getpid()}"
    redis = Redis.from_url(settings.redis_url)
    parents = IngestionQueue(redis, consumer=f"coordinator-{worker_id}")
    partitions = ExtractionQueue(redis, consumer=f"producer-{worker_id}")
    await parents.ensure_group()
    await partitions.ensure_group()
    objects = create_snapshot_object_store(settings)
    await objects.ensure_bucket()
    jobs = PostgresJobStore(
        lease_owner=worker_id,
        lease_seconds=settings.connector_ingestion_stale_after_seconds,
    )
    coordinator = ConnectorIngestionCoordinator(
        jobs=jobs,
        plans=SqlCoordinatorPlanStore(),
        publisher=partitions,
        object_store=objects,
        workspace=GitWorkspace(
            GitCommandRunner(),
            GitLimits(
                clone_timeout_seconds=(settings.connector_git_clone_timeout_seconds),
                fetch_timeout_seconds=(settings.connector_git_fetch_timeout_seconds),
                clone_depth=settings.connector_git_clone_depth,
            ),
        ),
        workspace_root=Path(settings.connector_ingestion_workspace),
        scan_limits=ScanLimits(
            chunk_size=settings.connector_ingestion_chunk_size,
            max_files=settings.connector_ingestion_max_files,
            max_file_bytes=settings.connector_ingestion_max_file_bytes,
            max_total_bytes=settings.connector_ingestion_max_total_bytes,
        ),
        partition_count=min(
            settings.connector_extraction_worker_count,
            settings.connector_ingestion_max_active_partitions_per_org,
        ),
    )
    try:
        while True:
            await parents.heartbeat()
            await redis.set(
                f"ecms:connector-ingestion:coordinator-health:{worker_id}",
                "1",
                ex=45,
            )
            delivery = await parents.read()
            if delivery is None:
                delivery = await parents.claim_stale(
                    min_idle_ms=(settings.connector_ingestion_stale_after_seconds * 1_000)
                )
            if delivery is None:
                continue
            try:
                await coordinator.coordinate(
                    job_id=delivery.job_id,
                    organization_id=delivery.organization_id,
                )
                await parents.acknowledge(delivery)
            except Exception as exc:
                retrying = await parents.retry_or_exhaust(
                    delivery,
                    max_deliveries=settings.connector_ingestion_max_deliveries,
                    acknowledge_exhausted=False,
                )
                if not retrying:
                    await jobs.fail(
                        delivery.job_id,
                        f"{type(exc).__name__}: {exc}"[:2_000],
                        retrying=False,
                    )
                    await parents.acknowledge(delivery)
                logger.exception(
                    "connector coordinator delivery failed",
                    extra={
                        "job_id": delivery.job_id,
                        "retrying": retrying,
                    },
                )
                await asyncio.sleep(2)
    finally:
        await redis.aclose()


def main() -> None:
    """Start the dedicated connector coordinator process."""
    logging.basicConfig(level=os.environ.get("ECMS_LOG_LEVEL", "INFO"))
    asyncio.run(run())


if __name__ == "__main__":
    main()
