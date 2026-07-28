"""Cache adapters (SECTION 106)."""

from __future__ import annotations

from typing import Protocol, cast, runtime_checkable

import redis.asyncio as aioredis

__all__ = ["Cache", "InMemoryCache", "RedisCache"]


@runtime_checkable
class Cache(Protocol):
    """A key-value cache.

    Operations:
        get: Return the value for a key, or None.
        set: Store a value with an optional TTL in seconds.
        delete: Remove a key.
    """

    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl: int | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...


class InMemoryCache:
    """In-memory cache for development and tests (TTL is not enforced)."""

    def __init__(self) -> None:
        """Initialize an empty cache."""
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        """Return the cached value for a key, or None."""
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Store a value (the in-memory cache ignores the TTL)."""
        self._store[key] = value

    async def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        self._store.pop(key, None)


class RedisCache:
    """Redis-backed cache adapter."""

    def __init__(self, client: aioredis.Redis) -> None:
        """Initialize the cache with a Redis client."""
        self._redis = client

    @classmethod
    def from_url(cls, url: str) -> RedisCache:
        """Create a cache connected to the given Redis URL."""
        return cls(aioredis.from_url(url, decode_responses=True))

    async def get(self, key: str) -> str | None:
        """Return the cached value for a key, or None."""
        return cast("str | None", await self._redis.get(key))

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Store a value with an optional TTL in seconds."""
        await self._redis.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        await self._redis.delete(key)

    async def close(self) -> None:
        """Close the Redis connection."""
        await self._redis.aclose()
