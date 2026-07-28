"""Tests for ``ecms.shared.interfaces``."""

from __future__ import annotations

from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent
from ecms.shared.interfaces import EventPublisher, HealthProbe


class _Probe:
    async def health(self) -> bool:
        return True

    async def ready(self) -> bool:
        return True


class _Bus:
    def __init__(self) -> None:
        self.events: list[BaseEvent] = []

    async def publish(self, event: BaseEvent) -> None:
        self.events.append(event)


def test_health_probe_is_runtime_checkable() -> None:
    assert isinstance(_Probe(), HealthProbe)


def test_event_publisher_is_runtime_checkable() -> None:
    assert isinstance(_Bus(), EventPublisher)


async def test_event_publisher_publishes() -> None:
    bus = _Bus()
    await bus.publish(BaseEvent(event_type="X", event_category=EventCategory.SYSTEM, producer="t"))
    assert len(bus.events) == 1
