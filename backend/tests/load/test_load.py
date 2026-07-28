"""Load tests (SECTION 84)."""

from __future__ import annotations

import asyncio

from ecms.events import InMemoryEventBus
from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent


def _event(index: int) -> BaseEvent:
    return BaseEvent(
        event_type=f"LoadEvent-{index}",
        event_category=EventCategory.SYSTEM,
        producer="load-test",
    )


async def test_event_bus_handles_many_events() -> None:
    bus = InMemoryEventBus()
    delivered = 0

    async def handler(_event: BaseEvent) -> None:
        nonlocal delivered
        delivered += 1

    bus.subscribe(handler)
    for index in range(1000):
        await bus.publish(_event(index))

    assert delivered == 1000
    assert bus.metrics().delivered == 1000


async def test_concurrent_publish() -> None:
    bus = InMemoryEventBus()
    delivered = 0

    async def handler(_event: BaseEvent) -> None:
        nonlocal delivered
        delivered += 1

    bus.subscribe(handler)
    await asyncio.gather(*(bus.publish(_event(index)) for index in range(500)))

    assert delivered == 500
