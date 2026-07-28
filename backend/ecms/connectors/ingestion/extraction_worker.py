"""Execution foundation for parallel connector extraction workers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from ecms.connectors.ingestion.parallel_queue import (
    DeliveryOutcome,
    ExtractionDelivery,
    ExtractionQueue,
)

PartitionHandler = Callable[[ExtractionDelivery], Awaitable[None]]
ExhaustedHandler = Callable[[ExtractionDelivery, Exception], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class ExtractionAttempt:
    """Observable result from processing at most one partition."""

    processed: bool
    outcome: DeliveryOutcome | None = None


class ExtractionWorker:
    """Claim and execute partition deliveries without knowing persistence details."""

    def __init__(
        self,
        queue: ExtractionQueue,
        handler: PartitionHandler,
        *,
        max_deliveries: int = 3,
        stale_after_ms: int = 60_000,
        on_exhausted: ExhaustedHandler | None = None,
    ) -> None:
        """Configure queue policy and the persistence-aware partition callback."""
        if max_deliveries < 1:
            raise ValueError("max_deliveries must be at least one")
        if stale_after_ms < 0:
            raise ValueError("stale_after_ms must not be negative")
        self._queue = queue
        self._handler = handler
        self._max_deliveries = max_deliveries
        self._stale_after_ms = stale_after_ms
        self._on_exhausted = on_exhausted

    async def process_one(self, *, block_ms: int = 4_000) -> ExtractionAttempt:
        """Prefer abandoned work, then process one fresh partition."""
        delivery = await self._queue.claim_stale(min_idle_ms=self._stale_after_ms)
        if delivery is None:
            delivery = await self._queue.read(block_ms=block_ms)
        if delivery is None:
            return ExtractionAttempt(processed=False)

        try:
            await self._handler(delivery)
        except Exception as exc:
            outcome = await self._queue.retry_or_exhaust(
                delivery,
                max_deliveries=self._max_deliveries,
                acknowledge_exhausted=False,
            )
            if outcome is DeliveryOutcome.EXHAUSTED:
                if self._on_exhausted is not None:
                    await self._on_exhausted(delivery, exc)
                await self._queue.acknowledge(delivery)
            return ExtractionAttempt(processed=True, outcome=outcome)

        await self._queue.acknowledge(delivery)
        return ExtractionAttempt(processed=True)
