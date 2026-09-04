"""Executable production process for bounded connector graph writes."""

from __future__ import annotations

import asyncio
import logging
import os
import socket

from redis.asyncio import Redis

from ecms.configuration.schemas.settings import get_settings
from ecms.connectors.ingestion.graph_semaphore import GraphWriteSemaphore
from ecms.connectors.ingestion.graph_writer import GraphWriter
from ecms.connectors.ingestion.graph_writer_runtime import (
    GraphBatchHandler,
    PostgresGraphBatchStore,
)
from ecms.connectors.ingestion.parallel_queue import GraphWriteQueue
from ecms.connectors.ingestion.worker import LegacyGraphChunkSink
from ecms.infrastructure.storage.factory import create_snapshot_object_store

logger = logging.getLogger(__name__)


async def run() -> None:
    """Consume graph batches with one globally enforced FalkorDB writer."""
    settings = get_settings()
    if not settings.connector_parallel_ingestion_enabled:
        raise RuntimeError("parallel connector ingestion is disabled")
    writer_id = f"{socket.gethostname()}-{os.getpid()}"
    redis = Redis.from_url(settings.redis_url)
    queue = GraphWriteQueue(redis, consumer=writer_id)
    await queue.ensure_group()
    objects = create_snapshot_object_store(settings)
    await objects.ensure_bucket()
    store = PostgresGraphBatchStore(lease_seconds=settings.connector_ingestion_stale_after_seconds)
    semaphore = GraphWriteSemaphore(
        redis,
        ttl_seconds=settings.connector_ingestion_stale_after_seconds,
    )
    writer = GraphWriter(
        queue,
        GraphBatchHandler(
            store=store,
            objects=objects,
            semaphore=semaphore,
            sink=LegacyGraphChunkSink(
                snapshot_timeout_seconds=(settings.connector_ingestion_snapshot_timeout_seconds)
            ),
            writer_id=writer_id,
        ),
        max_deliveries=settings.connector_ingestion_max_deliveries,
        stale_after_ms=settings.connector_ingestion_stale_after_seconds * 1_000,
        on_exhausted=store.exhausted,
    )
    try:
        while True:
            await redis.set(
                f"ecms:connector-ingestion:graph-writer-health:{writer_id}",
                "1",
                ex=45,
            )
            result = await writer.process_one()
            if result.processed and result.outcome is not None:
                logger.warning(
                    "graph delivery did not complete",
                    extra={"outcome": result.outcome},
                )
    finally:
        await redis.aclose()


def main() -> None:
    """Start the dedicated graph-writer process."""
    logging.basicConfig(level=os.environ.get("ECMS_LOG_LEVEL", "INFO"))
    asyncio.run(run())


if __name__ == "__main__":
    main()
