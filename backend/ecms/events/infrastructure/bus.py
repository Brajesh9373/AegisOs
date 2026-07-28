"""In-memory enterprise event bus (SECTION 99).

Provides publish/subscribe with type and category filters, at-least-once delivery with
retry and dead-lettering, idempotent publication by event id, replay from the event store,
and activity metrics. A Kafka adapter implementing the same port is added in the
infrastructure stage.
"""

from __future__ import annotations

from dataclasses import dataclass

from ecms.events.domain.models import BusMetrics, DeadLetter
from ecms.events.infrastructure.store import InMemoryEventStore
from ecms.events.interfaces.bus import EventHandler, EventStore
from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent
from ecms.shared.ids import new_id

__all__ = ["InMemoryEventBus"]


@dataclass
class _Subscription:
    """An event subscription with optional type and category filters."""

    subscription_id: str
    handler: EventHandler
    event_type: str | None
    category: EventCategory | None

    def matches(self, event: BaseEvent) -> bool:
        """Return whether this subscription should receive the given event."""
        if self.event_type is not None and event.event_type != self.event_type:
            return False
        return self.category is None or event.event_category == self.category


class InMemoryEventBus:
    """In-memory event bus with retry, dead-lettering, replay and metrics (SECTION 99)."""

    def __init__(self, *, store: EventStore | None = None, max_retries: int = 3) -> None:
        """Initialize the bus with an optional event store and retry budget."""
        self._store: EventStore = store or InMemoryEventStore()
        self._max_retries = max_retries
        self._subscriptions: dict[str, _Subscription] = {}
        self._dead_letters: list[DeadLetter] = []
        self._seen: set[str] = set()
        self._published = 0
        self._delivered = 0
        self._failed = 0
        self._dead_lettered = 0
        self._retried = 0

    async def publish(self, event: BaseEvent) -> None:
        """Persist and deliver an event, ignoring duplicates by event id."""
        if event.event_id in self._seen:
            return
        self._seen.add(event.event_id)
        await self._store.append(event)
        self._published += 1
        await self._deliver(event)

    def subscribe(
        self,
        handler: EventHandler,
        *,
        event_type: str | None = None,
        category: EventCategory | None = None,
    ) -> str:
        """Register a handler and return its subscription id."""
        subscription_id = new_id("sub")
        self._subscriptions[subscription_id] = _Subscription(
            subscription_id,
            handler,
            event_type,
            category,
        )
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription by id."""
        self._subscriptions.pop(subscription_id, None)

    async def history(self) -> list[BaseEvent]:
        """Return all persisted events."""
        return await self._store.read_all()

    async def replay(self, handler: EventHandler | None = None) -> int:
        """Re-deliver persisted events, returning the number replayed."""
        events = await self._store.read_all()
        for event in events:
            if handler is not None:
                await handler(event)
            else:
                await self._deliver(event)
        return len(events)

    def dead_letter(self) -> list[DeadLetter]:
        """Return events that failed delivery after exhausting retries."""
        return list(self._dead_letters)

    def metrics(self) -> BusMetrics:
        """Return the current bus activity counters."""
        return BusMetrics(
            published=self._published,
            delivered=self._delivered,
            failed=self._failed,
            dead_lettered=self._dead_lettered,
            retried=self._retried,
        )

    async def health(self) -> bool:
        """Return whether the bus is healthy."""
        return True

    async def _deliver(self, event: BaseEvent) -> None:
        for subscription in list(self._subscriptions.values()):
            if subscription.matches(event):
                await self._deliver_to(subscription, event)

    async def _deliver_to(self, subscription: _Subscription, event: BaseEvent) -> None:
        attempts = 0
        while True:
            try:
                await subscription.handler(event)
            except Exception as exc:  # the bus isolates subscriber failures
                attempts += 1
                self._failed += 1
                if attempts > self._max_retries:
                    self._dead_letters.append(
                        DeadLetter(event=event, error=str(exc), attempts=attempts),
                    )
                    self._dead_lettered += 1
                    return
                self._retried += 1
            else:
                self._delivered += 1
                return
