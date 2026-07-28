"""Base interface contracts (ports) for the shared kernel (SECTION 49/96).

These structural protocols are frozen contracts; concrete implementations are provided by
infrastructure adapters. Each protocol documents its operations at the class level.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ecms.shared.events import BaseEvent

__all__ = ["EventPublisher", "EventSubscriber", "HealthProbe", "Repository"]


@runtime_checkable
class HealthProbe(Protocol):
    """Liveness and readiness probe.

    Operations:
        health: Return ``True`` when the component is alive.
        ready: Return ``True`` when the component is ready to serve traffic.
    """

    async def health(self) -> bool: ...
    async def ready(self) -> bool: ...


class Repository[T](Protocol):
    """Generic persistence port for an aggregate of type ``T``.

    Operations:
        get: Return the entity with the given id, or ``None`` when absent.
        add: Persist a new entity.
        update: Persist changes to an existing entity.
        remove: Delete the entity with the given id.
        list_all: Return all entities.
    """

    async def get(self, entity_id: str) -> T | None: ...
    async def add(self, entity: T) -> None: ...
    async def update(self, entity: T) -> None: ...
    async def remove(self, entity_id: str) -> None: ...
    async def list_all(self) -> list[T]: ...


@runtime_checkable
class EventPublisher(Protocol):
    """Port for publishing events to the enterprise event bus.

    Operations:
        publish: Publish a single event to the bus.
    """

    async def publish(self, event: BaseEvent) -> None: ...


@runtime_checkable
class EventSubscriber(Protocol):
    """Port for handling events delivered by the enterprise event bus.

    Operations:
        handle: Process a delivered event idempotently.
    """

    async def handle(self, event: BaseEvent) -> None: ...
