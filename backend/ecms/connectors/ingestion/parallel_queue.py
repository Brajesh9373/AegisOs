"""Redis Streams transport primitives for partitioned connector ingestion.

Stream entries deliberately contain identifiers only.  Manifests, repository
paths, extracted records, credentials, and errors belong in durable stores and
are resolved by workers after claiming a delivery.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar, TypeVar

from redis.asyncio import Redis
from redis.exceptions import ResponseError

EXTRACTION_STREAM = "ecms:connector-ingestion:partitions"
EXTRACTION_GROUP = "connector-ingestion-extractors"
GRAPH_WRITE_STREAM = "ecms:connector-ingestion:graph-batches"
GRAPH_WRITE_GROUP = "connector-ingestion-graph-writers"
PARALLEL_RETRY_PREFIX = "ecms:connector-ingestion:parallel-retries:"


class DeliveryOutcome(StrEnum):
    """Result of recording a failed stream delivery."""

    RETRY = "retry"
    EXHAUSTED = "exhausted"


@dataclass(frozen=True, slots=True)
class ExtractionDelivery:
    """One partition assigned to an extraction worker."""

    message_id: str
    job_id: str
    manifest_id: str
    partition_id: str


@dataclass(frozen=True, slots=True)
class GraphWriteDelivery:
    """One durable staged batch assigned to a graph writer."""

    message_id: str
    job_id: str
    partition_id: str
    stage_batch_id: str


DeliveryT = TypeVar("DeliveryT", ExtractionDelivery, GraphWriteDelivery)


class _PartitionStream[DeliveryT]:
    """Typed, lease-friendly Redis Stream adapter."""

    stream: ClassVar[str]
    group: ClassVar[str]
    id_fields: ClassVar[tuple[str, ...]]
    delivery_type: ClassVar[type[DeliveryT]]

    def __init__(self, redis: Redis, *, consumer: str) -> None:
        if not consumer.strip():
            raise ValueError("consumer must not be empty")
        self._redis = redis
        self._consumer = consumer

    async def ensure_group(self) -> None:
        """Create this stream's consumer group exactly once."""
        try:
            await self._redis.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    async def _enqueue(self, identifiers: Mapping[str, str]) -> str:
        """Publish an ID-only message after validating its exact contract."""
        if set(identifiers) != set(self.id_fields):
            raise ValueError(f"stream fields must be exactly {self.id_fields}")
        if any(not value.strip() for value in identifiers.values()):
            raise ValueError("stream identifiers must not be empty")
        message_id = await self._redis.xadd(self.stream, dict(identifiers))
        return self._decode(message_id)

    async def read(self, *, block_ms: int = 4_000) -> DeliveryT | None:
        """Claim one previously undelivered message."""
        messages = await self._redis.xreadgroup(
            self.group,
            self._consumer,
            {self.stream: ">"},
            count=1,
            block=block_ms,
        )
        if not messages:
            return None
        return self._delivery(messages[0][1][0])

    async def claim_stale(self, *, min_idle_ms: int = 60_000) -> DeliveryT | None:
        """Transfer one abandoned delivery to this consumer."""
        result = await self._redis.xautoclaim(
            self.stream,
            self.group,
            self._consumer,
            min_idle_ms,
            start_id="0-0",
            count=1,
        )
        return self._delivery(result[1][0]) if result[1] else None

    async def acknowledge(self, delivery: DeliveryT) -> None:
        """Acknowledge a durably completed delivery."""
        await self._redis.xack(self.stream, self.group, delivery.message_id)
        await self._redis.delete(self._retry_key(delivery.message_id))

    async def retry_or_exhaust(
        self,
        delivery: DeliveryT,
        *,
        max_deliveries: int = 3,
        acknowledge_exhausted: bool = True,
    ) -> DeliveryOutcome:
        """Leave a failed delivery pending for reclaim, or ack after exhaustion."""
        if max_deliveries < 1:
            raise ValueError("max_deliveries must be at least one")
        retry_key = self._retry_key(delivery.message_id)
        failures = int(await self._redis.incr(retry_key))
        await self._redis.expire(retry_key, 86_400)
        if failures < max_deliveries:
            return DeliveryOutcome.RETRY
        if acknowledge_exhausted:
            await self.acknowledge(delivery)
        return DeliveryOutcome.EXHAUSTED

    def _retry_key(self, message_id: str) -> str:
        return f"{PARALLEL_RETRY_PREFIX}{self.stream}:{message_id}"

    @staticmethod
    def _decode(value: Any) -> str:
        return value.decode() if isinstance(value, bytes) else str(value)

    @classmethod
    def _delivery(cls, entry: tuple[Any, dict[Any, Any]]) -> DeliveryT:
        message_id, raw_fields = entry
        fields = {cls._decode(key): cls._decode(value) for key, value in raw_fields.items()}
        if set(fields) != set(cls.id_fields):
            raise ValueError(f"invalid {cls.stream} message fields: {tuple(sorted(fields))}")
        return cls.delivery_type(message_id=cls._decode(message_id), **fields)


class ExtractionQueue(_PartitionStream[ExtractionDelivery]):
    """Transport for disjoint manifest partitions."""

    stream = EXTRACTION_STREAM
    group = EXTRACTION_GROUP
    id_fields = ("job_id", "manifest_id", "partition_id")
    delivery_type = ExtractionDelivery

    async def enqueue(self, *, job_id: str, manifest_id: str, partition_id: str) -> str:
        """Publish an extraction partition by identifier."""
        return await self._enqueue(
            {
                "job_id": job_id,
                "manifest_id": manifest_id,
                "partition_id": partition_id,
            }
        )


class GraphWriteQueue(_PartitionStream[GraphWriteDelivery]):
    """Transport for immutable staged graph batches."""

    stream = GRAPH_WRITE_STREAM
    group = GRAPH_WRITE_GROUP
    id_fields = ("job_id", "partition_id", "stage_batch_id")
    delivery_type = GraphWriteDelivery

    async def enqueue(self, *, job_id: str, partition_id: str, stage_batch_id: str) -> str:
        """Publish a staged graph batch by identifier."""
        return await self._enqueue(
            {
                "job_id": job_id,
                "partition_id": partition_id,
                "stage_batch_id": stage_batch_id,
            }
        )
