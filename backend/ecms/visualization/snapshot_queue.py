"""Durable Redis Streams queue for knowledge-graph snapshot builds."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import ResponseError

STREAM = "ecms:knowledge-graph:snapshot-jobs"
GROUP = "knowledge-graph-snapshot-workers"
PENDING_PREFIX = "ecms:knowledge-graph:pending:"
DIRTY_PREFIX = "ecms:knowledge-graph:dirty:"
LOCK_PREFIX = "ecms:knowledge-graph:lock:"
RETRY_PREFIX = "ecms:knowledge-graph:retries:"
HEALTH_PREFIX = "ecms:knowledge-graph:worker-health:"
METRICS_KEY = "ecms:knowledge-graph:metrics"

__all__ = ["GraphSnapshotJob", "GraphSnapshotQueue"]


@dataclass(frozen=True)
class GraphSnapshotJob:
    """Decoded durable snapshot request."""

    message_id: str
    organization_id: str
    source_watermark: str | None


class GraphSnapshotQueue:
    """Coalesce connector bursts while retaining durable Redis Stream delivery."""

    def __init__(self, redis: Redis, *, consumer: str) -> None:
        """Bind a Redis connection and stable worker consumer name."""
        self._redis = redis
        self._consumer = consumer

    async def ensure_group(self) -> None:
        """Create the durable consumer group once."""
        try:
            await self._redis.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def enqueue(
        self,
        organization_id: str,
        *,
        source_watermark: str | None = None,
    ) -> bool:
        """Enqueue once per organization, marking a follow-up when already pending."""
        pending_key = f"{PENDING_PREFIX}{organization_id}"
        accepted = await self._redis.set(pending_key, "1", ex=3_600, nx=True)
        if not accepted:
            await self._redis.set(
                f"{DIRTY_PREFIX}{organization_id}",
                source_watermark or "changed",
                ex=7_200,
            )
            return False
        await self._redis.xadd(
            STREAM,
            {
                "organization_id": organization_id,
                "source_watermark": source_watermark or "",
                "requested_at": datetime.now(UTC).isoformat(),
            },
        )
        return True

    async def read(self, *, block_ms: int = 4_000) -> GraphSnapshotJob | None:
        """Read one new job assigned to this consumer."""
        messages = await self._redis.xreadgroup(
            GROUP,
            self._consumer,
            {STREAM: ">"},
            count=1,
            block=block_ms,
        )
        if not messages:
            return None
        _, entries = messages[0]
        message_id, fields = entries[0]
        decoded = self._decode_fields(fields)
        return GraphSnapshotJob(
            message_id=self._decode(message_id),
            organization_id=decoded["organization_id"],
            source_watermark=decoded.get("source_watermark") or None,
        )

    async def claim_stale(self, *, min_idle_ms: int = 30_000) -> GraphSnapshotJob | None:
        """Recover one job abandoned by a stopped or unhealthy worker."""
        result = await self._redis.xautoclaim(
            STREAM,
            GROUP,
            self._consumer,
            min_idle_ms,
            start_id="0-0",
            count=1,
        )
        entries = result[1]
        if not entries:
            return None
        message_id, fields = entries[0]
        decoded = self._decode_fields(fields)
        return GraphSnapshotJob(
            message_id=self._decode(message_id),
            organization_id=decoded["organization_id"],
            source_watermark=decoded.get("source_watermark") or None,
        )

    async def acquire_lock(self, organization_id: str, *, ttl_seconds: int = 60) -> bool:
        """Acquire the organization build lock."""
        return bool(
            await self._redis.set(
                f"{LOCK_PREFIX}{organization_id}",
                self._consumer,
                ex=ttl_seconds,
                nx=True,
            )
        )

    async def renew_lock(self, organization_id: str, *, ttl_seconds: int = 60) -> bool:
        """Extend a lock only when it is still owned by this worker."""
        script = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
          return redis.call('expire', KEYS[1], ARGV[2])
        end
        return 0
        """
        renewed = await self._redis.eval(
            script,
            1,
            f"{LOCK_PREFIX}{organization_id}",
            self._consumer,
            ttl_seconds,
        )
        return bool(renewed)

    async def heartbeat(self, *, ttl_seconds: int = 30) -> None:
        """Publish an expiring liveness marker for operational health checks."""
        await self._redis.set(
            f"{HEALTH_PREFIX}{self._consumer}",
            datetime.now(UTC).isoformat(),
            ex=ttl_seconds,
        )

    async def complete(self, job: GraphSnapshotJob) -> None:
        """Acknowledge a build and enqueue one coalesced follow-up if needed."""
        await self._redis.xack(STREAM, GROUP, job.message_id)
        await self._redis.delete(
            f"{LOCK_PREFIX}{job.organization_id}",
            f"{PENDING_PREFIX}{job.organization_id}",
            f"{RETRY_PREFIX}{job.message_id}",
        )
        dirty_key = f"{DIRTY_PREFIX}{job.organization_id}"
        watermark = await self._redis.getdel(dirty_key)
        if watermark is not None:
            await self.enqueue(
                job.organization_id,
                source_watermark=self._decode(watermark),
            )

    async def release_after_failure(
        self,
        job: GraphSnapshotJob,
        *,
        max_retries: int = 3,
    ) -> bool:
        """Release a failed job and return whether it remains eligible for retry."""
        await self._redis.delete(f"{LOCK_PREFIX}{job.organization_id}")
        retry_key = f"{RETRY_PREFIX}{job.message_id}"
        retries = await self._redis.incr(retry_key)
        await self._redis.hincrby(METRICS_KEY, "build_retries", 1)
        await self._redis.expire(retry_key, 86_400)
        if retries <= max_retries:
            return True

        await self._redis.xack(STREAM, GROUP, job.message_id)
        await self._redis.hincrby(METRICS_KEY, "builds_exhausted", 1)
        await self._redis.delete(
            retry_key,
            f"{PENDING_PREFIX}{job.organization_id}",
        )
        dirty_key = f"{DIRTY_PREFIX}{job.organization_id}"
        watermark = await self._redis.getdel(dirty_key)
        if watermark is not None:
            await self.enqueue(
                job.organization_id,
                source_watermark=self._decode(watermark),
            )
        return False

    @staticmethod
    def _decode(value: Any) -> str:
        return value.decode() if isinstance(value, bytes) else str(value)

    @classmethod
    def _decode_fields(cls, fields: dict[Any, Any]) -> dict[str, str]:
        return {cls._decode(key): cls._decode(value) for key, value in fields.items()}
