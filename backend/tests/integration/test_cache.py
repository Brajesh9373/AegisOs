"""Integration tests for cache adapters."""

from __future__ import annotations

import fakeredis.aioredis

from ecms.infrastructure.cache import InMemoryCache, RedisCache


async def test_in_memory_cache() -> None:
    cache = InMemoryCache()
    await cache.set("k", "v")
    assert await cache.get("k") == "v"
    await cache.delete("k")
    assert await cache.get("k") is None


async def test_redis_cache() -> None:
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    cache = RedisCache(client)
    await cache.set("k", "v")
    assert await cache.get("k") == "v"
    await cache.delete("k")
    assert await cache.get("k") is None
    await cache.close()
