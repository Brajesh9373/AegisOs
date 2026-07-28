"""Redis-backed global concurrency guard for connector graph writes."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from redis.asyncio import Redis
from redis.exceptions import WatchError

GRAPH_WRITE_SEMAPHORE_KEY = "ecms:connector-ingestion:graph-write-slot"


@dataclass(frozen=True, slots=True)
class GraphWriteLease:
    """Opaque ownership token for the single production graph-write slot."""

    token: str


class GraphWriteSemaphore:
    """Fail-closed global mutex with expiring ownership.

    The initial production topology permits one FalkorDB writer globally. The
    expiry prevents a dead process from holding the slot forever.
    """

    def __init__(
        self,
        redis: Redis,
        *,
        key: str = GRAPH_WRITE_SEMAPHORE_KEY,
        ttl_seconds: int = 120,
    ) -> None:
        """Bind the semaphore to Redis with a bounded recovery time."""
        if ttl_seconds < 1:
            raise ValueError("ttl_seconds must be positive")
        self._redis = redis
        self._key = key
        self._ttl_seconds = ttl_seconds

    async def acquire(self) -> GraphWriteLease | None:
        """Acquire the slot without waiting, returning an opaque lease."""
        token = uuid4().hex
        acquired = await self._redis.set(
            self._key,
            token,
            ex=self._ttl_seconds,
            nx=True,
        )
        return GraphWriteLease(token) if acquired else None

    async def renew(self, lease: GraphWriteLease) -> bool:
        """Extend an owned slot without allowing another owner to be renewed."""
        async with self._redis.pipeline(transaction=True) as pipeline:
            while True:
                try:
                    await pipeline.watch(self._key)
                    current = await pipeline.get(self._key)
                    if self._decode(current) != lease.token:
                        await pipeline.reset()
                        return False
                    pipeline.multi()
                    pipeline.expire(self._key, self._ttl_seconds)
                    result = await pipeline.execute()
                    return bool(result and result[0])
                except WatchError:
                    continue

    async def release(self, lease: GraphWriteLease) -> bool:
        """Delete the slot only when the caller still owns it."""
        async with self._redis.pipeline(transaction=True) as pipeline:
            while True:
                try:
                    await pipeline.watch(self._key)
                    current = await pipeline.get(self._key)
                    if self._decode(current) != lease.token:
                        await pipeline.reset()
                        return False
                    pipeline.multi()
                    pipeline.delete(self._key)
                    result = await pipeline.execute()
                    return bool(result and result[0])
                except WatchError:
                    continue

    @staticmethod
    def _decode(value: bytes | str | None) -> str | None:
        if isinstance(value, bytes):
            return value.decode()
        return value
