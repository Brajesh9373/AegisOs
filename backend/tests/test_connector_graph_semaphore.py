from __future__ import annotations

import fakeredis.aioredis

from ecms.connectors.ingestion.graph_semaphore import GraphWriteSemaphore


async def test_only_one_graph_writer_owns_global_slot() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    first = GraphWriteSemaphore(redis, ttl_seconds=10)
    second = GraphWriteSemaphore(redis, ttl_seconds=10)

    lease = await first.acquire()
    assert lease is not None
    assert await second.acquire() is None
    assert await first.renew(lease)
    assert await first.release(lease)
    assert await second.acquire() is not None


async def test_stale_owner_cannot_release_new_lease() -> None:
    redis = fakeredis.aioredis.FakeRedis()
    semaphore = GraphWriteSemaphore(redis, ttl_seconds=10)
    stale = await semaphore.acquire()
    assert stale is not None
    await redis.delete("ecms:connector-ingestion:graph-write-slot")
    current = await semaphore.acquire()
    assert current is not None

    assert not await semaphore.release(stale)
    assert await semaphore.renew(current)
