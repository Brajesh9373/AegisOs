"""Base domain model types for the shared kernel (SECTION 96).

These provide the common Pydantic configuration, timestamping, aggregate-root domain-event
collection, and small shared value objects reused by every domain model.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from ecms.shared.enums import SecurityClassification
from ecms.shared.time import utcnow

__all__ = [
    "AggregateRoot",
    "Attachment",
    "DomainModel",
    "ImmutableModel",
    "SecurityPolicy",
    "TimestampedModel",
]


class DomainModel(BaseModel):
    """Base for mutable domain models with strict validation semantics."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ImmutableModel(BaseModel):
    """Base for immutable domain models (frozen, equality and hashing by value)."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        frozen=True,
    )


class TimestampedModel(DomainModel):
    """Mutable domain model carrying creation and modification timestamps."""

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class AggregateRoot(TimestampedModel):
    """Base for aggregate roots that record domain events for later publication.

    Aggregates accumulate domain events during a unit of work; the application layer
    publishes them to the event bus after the aggregate is persisted.
    """

    _pending_events: list[object] = PrivateAttr(default_factory=list)

    def register_event(self, event: object) -> None:
        """Record a domain event to be published after this aggregate is persisted."""
        self._pending_events.append(event)

    def collect_events(self) -> list[object]:
        """Return the pending domain events and clear the buffer."""
        events = list(self._pending_events)
        self._pending_events.clear()
        return events


class Attachment(DomainModel):
    """A supporting file attached to a knowledge object (SECTION 22)."""

    name: str
    mime_type: str | None = None
    uri: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)


class SecurityPolicy(DomainModel):
    """Data-centric access policy attached to knowledge (SECTION 9/79).

    Knowledge owns its permissions; applications do not.
    """

    classification: SecurityClassification = SecurityClassification.INTERNAL
    allowed_roles: list[str] = Field(default_factory=list)
    allowed_principals: list[str] = Field(default_factory=list)
