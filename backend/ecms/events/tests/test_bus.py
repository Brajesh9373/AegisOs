"""Tests for the in-memory event bus."""

from __future__ import annotations

from ecms.events import InMemoryEventBus
from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent


def _event(event_type: str = "X", category: EventCategory = EventCategory.SYSTEM) -> BaseEvent:
    return BaseEvent(event_type=event_type, event_category=category, producer="test")


async def test_publish_delivers_to_subscriber() -> None:
    bus = InMemoryEventBus()
    received: list[BaseEvent] = []

    async def handler(event: BaseEvent) -> None:
        received.append(event)

    bus.subscribe(handler)
    await bus.publish(_event())
    assert len(received) == 1
    assert bus.metrics().published == 1
    assert bus.metrics().delivered == 1


async def test_event_type_filter() -> None:
    bus = InMemoryEventBus()
    got: list[BaseEvent] = []

    async def handler(event: BaseEvent) -> None:
        got.append(event)

    bus.subscribe(handler, event_type="Wanted")
    await bus.publish(_event(event_type="Other"))
    await bus.publish(_event(event_type="Wanted"))
    assert len(got) == 1


async def test_category_filter() -> None:
    bus = InMemoryEventBus()
    got: list[BaseEvent] = []

    async def handler(event: BaseEvent) -> None:
        got.append(event)

    bus.subscribe(handler, category=EventCategory.KNOWLEDGE)
    await bus.publish(_event(category=EventCategory.SYSTEM))
    await bus.publish(_event(category=EventCategory.KNOWLEDGE))
    assert len(got) == 1


async def test_unsubscribe_stops_delivery() -> None:
    bus = InMemoryEventBus()
    got: list[BaseEvent] = []

    async def handler(event: BaseEvent) -> None:
        got.append(event)

    subscription = bus.subscribe(handler)
    bus.unsubscribe(subscription)
    await bus.publish(_event())
    assert got == []


async def test_publish_is_idempotent() -> None:
    bus = InMemoryEventBus()
    got: list[BaseEvent] = []

    async def handler(event: BaseEvent) -> None:
        got.append(event)

    bus.subscribe(handler)
    event = _event()
    await bus.publish(event)
    await bus.publish(event)
    assert len(got) == 1
    assert len(await bus.history()) == 1


async def test_retry_then_dead_letter() -> None:
    bus = InMemoryEventBus(max_retries=2)

    async def failing(_event: BaseEvent) -> None:
        raise RuntimeError("boom")

    bus.subscribe(failing)
    await bus.publish(_event())
    assert len(bus.dead_letter()) == 1
    metrics = bus.metrics()
    assert metrics.dead_lettered == 1
    assert metrics.retried == 2
    assert metrics.failed == 3


async def test_replay_redelivers_events() -> None:
    bus = InMemoryEventBus()
    await bus.publish(_event(event_type="A"))
    await bus.publish(_event(event_type="B"))
    replayed: list[str] = []

    async def handler(event: BaseEvent) -> None:
        replayed.append(event.event_type)

    count = await bus.replay(handler)
    assert count == 2
    assert replayed == ["A", "B"]


async def test_health_is_true() -> None:
    assert await InMemoryEventBus().health() is True
