"""Tests for the durable event store and Kafka topic taxonomy (SECTION 65/249)."""

from __future__ import annotations

from ecms.events import (
    InMemoryEventBus,
    PersistentEventStore,
    all_topics,
    event_topic,
)
from ecms.persistence import Database
from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent


async def _make_db() -> Database:
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_all()
    return database


def _event(
    event_type: str = "TaskCreated",
    category: EventCategory = EventCategory.TASK,
    correlation_id: str = "corr-1",
) -> BaseEvent:
    return BaseEvent(
        event_type=event_type,
        event_category=category,
        producer="test",
        correlation_id=correlation_id,
    )


async def test_append_and_read_all_preserve_order() -> None:
    database = await _make_db()
    store = PersistentEventStore(database)
    await store.append(_event("A"))
    await store.append(_event("B"))
    events = await store.read_all()
    assert [event.event_type for event in events] == ["A", "B"]
    await database.dispose()


async def test_read_by_correlation_filters_chain() -> None:
    database = await _make_db()
    store = PersistentEventStore(database)
    await store.append(_event("A", correlation_id="c1"))
    await store.append(_event("B", correlation_id="c2"))
    await store.append(_event("C", correlation_id="c1"))
    chain = await store.read_by_correlation("c1")
    assert [event.event_type for event in chain] == ["A", "C"]
    await database.dispose()


async def test_bus_replay_rebuilds_from_durable_store() -> None:
    database = await _make_db()
    store = PersistentEventStore(database)
    producing_bus = InMemoryEventBus(store=store)
    await producing_bus.publish(_event("A"))
    await producing_bus.publish(_event("B"))

    rebuilt_bus = InMemoryEventBus(store=store)
    replayed: list[str] = []

    async def handler(event: BaseEvent) -> None:
        replayed.append(event.event_type)

    count = await rebuilt_bus.replay(handler)
    assert count == 2
    assert replayed == ["A", "B"]
    await database.dispose()


def test_topic_taxonomy_covers_every_category() -> None:
    assert event_topic(EventCategory.TASK) == "ecms.task"
    assert event_topic(EventCategory.KNOWLEDGE, prefix="acme") == "acme.knowledge"
    topics = all_topics()
    assert "ecms.reflection" in topics
    assert len(topics) == len(list(EventCategory))
