"""Base enterprise event contract (SECTION 33).

Every event is immutable, append-only, versioned and traceable. Concrete event types are
defined by their owning subsystems; the foundation provides only this base contract and a
helper to build events from the ambient request context.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ecms import __version__
from ecms.shared.context import current_context, get_correlation_id
from ecms.shared.enums import EventCategory, SecurityClassification
from ecms.shared.ids import new_id
from ecms.shared.time import utcnow

__all__ = ["BaseEvent", "make_event"]


def _event_id() -> str:
    return new_id("evt")


class BaseEvent(BaseModel):
    """Immutable base contract inherited by every enterprise event (SECTION 33)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(default_factory=_event_id)
    event_type: str
    event_version: int = Field(default=1, ge=1)
    event_category: EventCategory
    organization_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    session_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    timestamp: datetime = Field(default_factory=utcnow)
    producer: str
    producer_version: str = __version__
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    security_classification: SecurityClassification = SecurityClassification.INTERNAL
    signature: str | None = None
    trace_context: dict[str, str] = Field(default_factory=dict)


def make_event(
    event_type: str,
    event_category: EventCategory,
    producer: str,
    *,
    payload: dict[str, Any] | None = None,
    causation_id: str | None = None,
) -> BaseEvent:
    """Create a :class:`BaseEvent` populated from the current request context.

    The correlation id, session id, task id and trace context are taken from the ambient
    context so that the event can be traced across the workflow that produced it.

    Args:
        event_type: The official event name describing a fact (e.g. ``"KnowledgePromoted"``).
        event_category: The category the event belongs to.
        producer: The name of the originating service.
        payload: Optional event-specific data.
        causation_id: The id of the event that caused this event, if any.

    Returns:
        A new immutable event.
    """
    ctx = current_context()
    trace_context = {
        key: value
        for key, value in (("trace_id", ctx.trace_id), ("span_id", ctx.span_id))
        if value is not None
    }
    return BaseEvent(
        event_type=event_type,
        event_category=event_category,
        producer=producer,
        payload=payload or {},
        correlation_id=ctx.correlation_id or get_correlation_id(),
        causation_id=causation_id,
        session_id=ctx.session_id,
        task_id=ctx.task_id,
        trace_context=trace_context,
    )
