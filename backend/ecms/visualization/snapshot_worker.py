"""Dedicated Redis Streams worker for knowledge-graph snapshots."""

from __future__ import annotations

import asyncio
import logging
import os
import socket
from time import perf_counter

from redis.asyncio import Redis

from ecms.configuration.schemas.settings import get_settings
from ecms.infrastructure.storage.factory import create_snapshot_object_store
from ecms.persistence.database.rest_session import db_session
from ecms.visualization.snapshot_queue import METRICS_KEY, GraphSnapshotQueue
from ecms.visualization.snapshot_service import GraphSnapshotService, LegacyFalkorGraphSource

logger = logging.getLogger(__name__)


async def _maintain_lock(queue: GraphSnapshotQueue, organization_id: str) -> None:
    """Renew the build lock and worker heartbeat while a snapshot is running."""
    while True:
        await asyncio.sleep(20)
        await queue.heartbeat()
        if not await queue.renew_lock(organization_id):
            raise RuntimeError(f"lost snapshot build lock for {organization_id}")


async def run_worker() -> None:
    """Consume durable snapshot jobs until the process is terminated."""
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    consumer = f"{socket.gethostname()}-{os.getpid()}"
    queue = GraphSnapshotQueue(redis, consumer=consumer)
    store = create_snapshot_object_store(settings)
    await store.ensure_bucket()
    await queue.ensure_group()
    await queue.heartbeat()
    logger.info("knowledge graph snapshot worker ready: %s", consumer)
    try:
        while True:
            job = await queue.read()
            await queue.heartbeat()
            if job is None:
                job = await queue.claim_stale()
                if job is None:
                    continue
            if not await queue.acquire_lock(job.organization_id):
                await asyncio.sleep(1)
                continue
            lock_maintenance = asyncio.create_task(_maintain_lock(queue, job.organization_id))
            build_started = perf_counter()
            try:
                async with asyncio.timeout(1_800):
                    async with db_session() as session:
                        service = GraphSnapshotService(
                            session=session,
                            object_store=store,
                            graph_source=LegacyFalkorGraphSource(),
                        )
                        await service.build(
                            organization_id=job.organization_id,
                            source_watermark=job.source_watermark,
                        )
                        removed = await service.apply_retention(
                            organization_id=job.organization_id,
                        )
                        if removed:
                            logger.info(
                                "knowledge graph retention removed %s old snapshots for %s",
                                removed,
                                job.organization_id,
                            )
                await queue.complete(job)
                duration = perf_counter() - build_started
                await redis.hincrby(METRICS_KEY, "builds_completed", 1)
                await redis.hincrbyfloat(
                    METRICS_KEY,
                    "build_duration_seconds_total",
                    duration,
                )
                await redis.hset(
                    METRICS_KEY,
                    mapping={"build_duration_seconds_last": duration},
                )
                logger.info("knowledge graph snapshot completed for %s", job.organization_id)
            except Exception:
                duration = perf_counter() - build_started
                await redis.hincrby(METRICS_KEY, "builds_failed", 1)
                await redis.hset(
                    METRICS_KEY,
                    mapping={"build_duration_seconds_last": duration},
                )
                retrying = await queue.release_after_failure(job)
                logger.exception(
                    "knowledge graph snapshot failed for %s (retrying=%s)",
                    job.organization_id,
                    retrying,
                )
                await asyncio.sleep(5)
            finally:
                lock_maintenance.cancel()
                await asyncio.gather(lock_maintenance, return_exceptions=True)
    finally:
        await redis.aclose()


def main() -> None:
    """Run the dedicated worker process."""
    logging.basicConfig(level=os.environ.get("ECMS_LOG_LEVEL", "INFO"))
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
