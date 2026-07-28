"""Shared graph-change hook used by connector persistence paths."""

from __future__ import annotations

import logging

from redis.asyncio import Redis

from ecms.configuration.schemas.settings import get_settings
from ecms.visualization.snapshot_queue import GraphSnapshotQueue

logger = logging.getLogger(__name__)


async def snapshot_after_graph_write(
    *,
    persisted: bool,
    success_count: int,
    source: str,
    revision: str | None = None,
    organization_id: str = "default",
) -> bool:
    """Publish only successful durable graph mutations and isolate queue outages."""
    if not persisted or success_count <= 0:
        return False
    try:
        return await graph_changed(
            organization_id,
            source=source,
            revision=revision,
        )
    except Exception:
        logger.exception(
            "knowledge graph snapshot trigger failed after %s write",
            source,
        )
        return False


async def graph_changed(
    organization_id: str = "default",
    *,
    source: str,
    revision: str | None = None,
) -> bool:
    """Request a coalesced snapshot after a successful graph mutation."""
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    try:
        queue = GraphSnapshotQueue(redis, consumer="producer")
        return await queue.enqueue(
            organization_id,
            source_watermark=f"{source}:{revision or 'changed'}",
        )
    finally:
        await redis.aclose()
