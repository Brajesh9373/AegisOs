"""Durable, append-only SQL event store enabling replay and rebuild (SECTION 65/67).

Backing the event bus with this store makes the platform event-sourced: because
events are only ever appended, the entire system state can be reconstructed by
replaying the store (SECTION 65). It implements the :class:`EventStore` port, so
it drops into the existing bus without changing publishers or subscribers.
"""

from __future__ import annotations

from sqlalchemy import select

from ecms.events.infrastructure.serialization import (
    deserialize_event,
    serialize_event,
)
from ecms.persistence.database.engine import Database
from ecms.persistence.models.event import EventRecord
from ecms.shared.events import BaseEvent

__all__ = ["PersistentEventStore"]


class PersistentEventStore:
    """An append-only event store backed by a relational database (SECTION 67)."""

    def __init__(self, database: Database) -> None:
        """Initialize the store against a database."""
        self._database = database

    async def append(self, event: BaseEvent) -> None:
        """Persist an event; the store is never updated or deleted."""
        async with self._database.session() as session:
            session.add(
                EventRecord(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    event_category=event.event_category.value,
                    correlation_id=event.correlation_id,
                    payload=serialize_event(event),
                )
            )

    async def read_all(self) -> list[BaseEvent]:
        """Return every persisted event in global insertion order."""
        async with self._database.session() as session:
            result = await session.execute(select(EventRecord).order_by(EventRecord.sequence))
            return [deserialize_event(record.payload) for record in result.scalars()]

    async def read_by_correlation(self, correlation_id: str) -> list[BaseEvent]:
        """Return persisted events for one correlation chain, in order."""
        async with self._database.session() as session:
            result = await session.execute(
                select(EventRecord)
                .where(EventRecord.correlation_id == correlation_id)
                .order_by(EventRecord.sequence)
            )
            return [deserialize_event(record.payload) for record in result.scalars()]
