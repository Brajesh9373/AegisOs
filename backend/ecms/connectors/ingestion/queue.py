"""Redis Streams transport for connector-ingestion jobs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import ResponseError

STREAM = "ecms:connector-ingestion:jobs"
GROUP = "connector-ingestion-workers"
HEALTH_PREFIX = "ecms:connector-ingestion:worker-health:"
RETRY_PREFIX = "ecms:connector-ingestion:retries:"
METRICS_KEY = "ecms:connector-ingestion:metrics"


@dataclass(frozen=True)
class IngestionJob:
    """A job delivery claimed from the durable stream."""

    message_id: str
    job_id: str
    organization_id: str


class IngestionQueue:
    """Small Redis Streams adapter with stale-delivery recovery."""

    def __init__(self, redis: Redis, *, consumer: str) -> None:
        """Bind a Redis connection and stable consumer name."""
        self._redis = redis
        self._consumer = consumer

    async def ensure_group(self) -> None:
        """Create the consumer group exactly once."""
        try:
            await self._redis.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def enqueue(self, job_id: str, organization_id: str) -> str:
        """Publish identifiers only; connector credentials remain in the job store."""
        message_id = await self._redis.xadd(
            STREAM,
            {
                "job_id": job_id,
                "organization_id": organization_id,
                "requested_at": datetime.now(UTC).isoformat(),
            },
        )
        return self._decode(message_id)

    async def read(self, *, block_ms: int = 4_000) -> IngestionJob | None:
        """Read one new delivery for this consumer."""
        messages = await self._redis.xreadgroup(
            GROUP, self._consumer, {STREAM: ">"}, count=1, block=block_ms
        )
        if not messages:
            return None
        return self._job(messages[0][1][0])

    async def claim_stale(self, *, min_idle_ms: int = 60_000) -> IngestionJob | None:
        """Claim one delivery abandoned by an unhealthy worker."""
        result = await self._redis.xautoclaim(
            STREAM,
            GROUP,
            self._consumer,
            min_idle_ms,
            start_id="0-0",
            count=1,
        )
        return self._job(result[1][0]) if result[1] else None

    async def acknowledge(self, job: IngestionJob) -> None:
        """Acknowledge a terminal delivery."""
        await self._redis.xack(STREAM, GROUP, job.message_id)
        await self._redis.delete(f"{RETRY_PREFIX}{job.message_id}")

    async def retry_or_exhaust(
        self,
        job: IngestionJob,
        *,
        max_deliveries: int = 3,
        acknowledge_exhausted: bool = True,
    ) -> bool:
        """Record a failed delivery and acknowledge it after exhaustion."""
        key = f"{RETRY_PREFIX}{job.message_id}"
        attempts = await self._redis.incr(key)
        await self._redis.expire(key, 86_400)
        await self._redis.hincrby(METRICS_KEY, "delivery_retries", 1)
        if attempts < max_deliveries:
            return True
        if acknowledge_exhausted:
            await self.acknowledge(job)
        await self._redis.hincrby(METRICS_KEY, "deliveries_exhausted", 1)
        return False

    async def heartbeat(self, *, ttl_seconds: int = 30) -> None:
        """Publish an expiring worker liveness marker."""
        await self._redis.set(
            f"{HEALTH_PREFIX}{self._consumer}",
            datetime.now(UTC).isoformat(),
            ex=ttl_seconds,
        )

    async def increment_metric(self, name: str) -> None:
        """Increment an operational counter without exposing the Redis client."""
        await self._redis.hincrby(METRICS_KEY, name, 1)

    async def set_metric(self, name: str, value: float) -> None:
        """Record the latest value of an operational measurement."""
        await self._redis.hset(METRICS_KEY, name, str(value))

    @staticmethod
    def _decode(value: Any) -> str:
        return value.decode() if isinstance(value, bytes) else str(value)

    @classmethod
    def _job(cls, entry: tuple[Any, dict[Any, Any]]) -> IngestionJob:
        message_id, fields = entry
        decoded = {cls._decode(key): cls._decode(value) for key, value in fields.items()}
        return IngestionJob(
            message_id=cls._decode(message_id),
            job_id=decoded["job_id"],
            organization_id=decoded["organization_id"],
        )
