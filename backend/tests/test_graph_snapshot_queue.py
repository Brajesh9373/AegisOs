from __future__ import annotations

import fakeredis.aioredis
import pytest

from ecms.visualization.snapshot_queue import GraphSnapshotQueue


@pytest.mark.asyncio
async def test_queue_coalesces_and_enqueues_one_follow_up() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    queue = GraphSnapshotQueue(redis, consumer="test-worker")
    await queue.ensure_group()

    assert await queue.enqueue("org-1", source_watermark="git:1") is True
    assert await queue.enqueue("org-1", source_watermark="git:2") is False
    job = await queue.read(block_ms=1)
    assert job is not None
    assert job.source_watermark == "git:1"
    assert await queue.acquire_lock("org-1") is True
    await queue.complete(job)

    follow_up = await queue.read(block_ms=1)
    assert follow_up is not None
    assert follow_up.source_watermark == "git:2"
    await redis.aclose()


@pytest.mark.asyncio
async def test_queue_recovers_an_abandoned_pending_job() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    first_worker = GraphSnapshotQueue(redis, consumer="worker-that-stopped")
    recovery_worker = GraphSnapshotQueue(redis, consumer="replacement-worker")
    await first_worker.ensure_group()

    await first_worker.enqueue("org-1")
    abandoned = await first_worker.read(block_ms=1)
    assert abandoned is not None

    recovered = await recovery_worker.claim_stale(min_idle_ms=0)
    assert recovered == abandoned
    await redis.aclose()


@pytest.mark.asyncio
async def test_build_lock_has_short_crash_recovery_ttl() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    queue = GraphSnapshotQueue(redis, consumer="worker")
    assert await queue.acquire_lock("org-1") is True
    ttl = await redis.ttl("ecms:knowledge-graph:lock:org-1")
    assert 0 < ttl <= 60
    await redis.aclose()


@pytest.mark.asyncio
async def test_queue_stops_retrying_after_the_bounded_limit() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    queue = GraphSnapshotQueue(redis, consumer="test-worker")
    await queue.ensure_group()
    await queue.enqueue("org-1")
    job = await queue.read(block_ms=1)
    assert job is not None

    assert await queue.release_after_failure(job, max_retries=1) is True
    assert await queue.release_after_failure(job, max_retries=1) is False
    assert await queue.enqueue("org-1") is True
    await redis.aclose()
