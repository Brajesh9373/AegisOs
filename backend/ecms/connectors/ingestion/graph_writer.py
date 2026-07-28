"""Bounded graph-writer execution for immutable staged ingestion batches."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ecms.connectors.ingestion.parallel_queue import (
    DeliveryOutcome,
    GraphWriteDelivery,
    GraphWriteQueue,
)

BatchHandler = Callable[[GraphWriteDelivery], Awaitable[None]]
ExhaustedHandler = Callable[[GraphWriteDelivery, Exception], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class GraphWriteAttempt:
    """Observable result from processing at most one staged batch."""

    processed: bool
    outcome: DeliveryOutcome | None = None


class GraphWriter:
    """Consume staged batches serially within one worker process.

    Cross-process exclusivity belongs to the durable batch lease acquired by the
    handler. This class never accepts extracted payloads from Redis.
    """

    def __init__(
        self,
        queue: GraphWriteQueue,
        handler: BatchHandler,
        *,
        max_deliveries: int = 3,
        stale_after_ms: int = 60_000,
        on_exhausted: ExhaustedHandler | None = None,
    ) -> None:
        """Configure retry and stale-delivery policy for one bounded writer."""
        if max_deliveries < 1:
            raise ValueError("max_deliveries must be at least one")
        if stale_after_ms < 0:
            raise ValueError("stale_after_ms must not be negative")
        self._queue = queue
        self._handler = handler
        self._max_deliveries = max_deliveries
        self._stale_after_ms = stale_after_ms
        self._on_exhausted = on_exhausted

    async def process_one(self, *, block_ms: int = 4_000) -> GraphWriteAttempt:
        """Prefer abandoned work before reading a new staged-batch delivery."""
        delivery = await self._queue.claim_stale(min_idle_ms=self._stale_after_ms)
        if delivery is None:
            delivery = await self._queue.read(block_ms=block_ms)
        if delivery is None:
            return GraphWriteAttempt(processed=False)
        try:
            await self._handler(delivery)
        except Exception as exc:
            outcome = await self._queue.retry_or_exhaust(
                delivery,
                max_deliveries=self._max_deliveries,
                acknowledge_exhausted=False,
            )
            if outcome is DeliveryOutcome.EXHAUSTED:
                if self._on_exhausted:
                    await self._on_exhausted(delivery, exc)
                await self._queue.acknowledge(delivery)
            return GraphWriteAttempt(processed=True, outcome=outcome)
        await self._queue.acknowledge(delivery)
        return GraphWriteAttempt(processed=True)
