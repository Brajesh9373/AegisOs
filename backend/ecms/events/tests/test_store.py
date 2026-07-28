"""Tests for the in-memory event store."""

from __future__ import annotations

from ecms.events import InMemoryEventStore
from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent


async def test_append_and_read_all() -> None:
    store = InMemoryEventStore()
    event = BaseEvent(event_type="X", event_category=EventCategory.SYSTEM, producer="t")
    await store.append(event)
    assert await store.read_all() == [event]
