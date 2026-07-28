"""Event bus and event store ports (SECTION 68/99)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

from ecms.events.domain.models import BusMetrics, DeadLetter
from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent

__all__ = ["EventBus", "EventHandler", "EventStore"]

EventHandler = Callable[[BaseEvent], Awaitable[None]]


@runtime_checkable
class EventStore(Protocol):
    """Append-only, replayable persistence hook for events (SECTION 99).

    Operations:
        append: Persist an event.
        read_all: Return all persisted events in insertion order.
    """

    async def append(self, event: BaseEvent) -> None: ...
    async def read_all(self) -> list[BaseEvent]: ...


class EventBus(Protocol):
    """Enterprise event bus (SECTION 68).

    Operations:
        publish: Persist and deliver an event to matching subscribers.
        subscribe: Register a handler (optionally filtered); returns a subscription id.
        unsubscribe: Remove a subscription by id.
        history: Return all persisted events.
        replay: Re-deliver persisted events; returns the count replayed.
        dead_letter: Return events that failed delivery after retries.
        metrics: Return bus activity counters.
        health: Return whether the bus is healthy.
    """

    async def publish(self, event: BaseEvent) -> None: ...
    def subscribe(
        self,
        handler: EventHandler,
        *,
        event_type: str | None = None,
        category: EventCategory | None = None,
    ) -> str: ...
    def unsubscribe(self, subscription_id: str) -> None: ...
    async def history(self) -> list[BaseEvent]: ...
    async def replay(self, handler: EventHandler | None = None) -> int: ...
    def dead_letter(self) -> list[DeadLetter]: ...
    def metrics(self) -> BusMetrics: ...
    async def health(self) -> bool: ...
