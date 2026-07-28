"""In-memory event store (SECTION 99)."""

from __future__ import annotations

from ecms.shared.events import BaseEvent

__all__ = ["InMemoryEventStore"]


class InMemoryEventStore:
    """An append-only, in-memory event store for development and tests."""

    def __init__(self) -> None:
        """Initialize an empty event store."""
        self._events: list[BaseEvent] = []

    async def append(self, event: BaseEvent) -> None:
        """Append an event to the store."""
        self._events.append(event)

    async def read_all(self) -> list[BaseEvent]:
        """Return all persisted events in insertion order."""
        return list(self._events)
