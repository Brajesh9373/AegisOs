"""Telemetry envelope — the Mission Control WebSocket wire contract (SECTION 195/234).

Every event delivered to the frontend is wrapped in a :class:`TelemetryEnvelope`. The
envelope is the single, stable contract consumed by the frontend Unified Event Pipeline
(Frontend Master Prompt SECTION 422/426): the ``sequence`` field gives a monotonic ordering
key, ``event_id`` gives a deduplication key, and ``category`` maps directly onto the
frontend event router's channels. Scoping ids (organization/workspace/session/task/agent)
let the client route an event to the correct feature store.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from ecms.shared.events import BaseEvent

__all__ = ["TelemetryEnvelope", "to_envelope"]


class TelemetryEnvelope(BaseModel):
    """Immutable, self-describing WebSocket message wrapping one enterprise event.

    Attributes:
        kind: Discriminator identifying this frame as an ``event`` frame (control frames
            such as ``ready``/``pong`` use other ``kind`` values and are not envelopes).
        sequence: Monotonic broadcast-order key assigned by the telemetry bridge. The
            frontend orders by this value and requests replay of everything after its last
            seen sequence on reconnect.
        event_id: Globally unique event id, used by the frontend to deduplicate.
        type: The originating event type (e.g. ``"KnowledgePromoted"``).
        category: The event category value; one of the frontend router channels.
        timestamp: ISO-8601 timestamp of the originating event.
        organization_id: Owning organization, when scoped.
        workspace_id: Owning workspace, when scoped.
        project_id: Owning project, when scoped.
        session_id: Owning session, used for session-scoped channel routing.
        task_id: Related task, when applicable.
        agent_id: Related agent, when applicable.
        correlation_id: Correlation chain id, used to group a workflow's events.
        causation_id: The event that caused this event, when applicable.
        classification: Security classification of the originating event.
        payload: The event-specific data.
    """

    model_config = ConfigDict(frozen=True)

    kind: Literal["event"] = "event"
    sequence: int
    event_id: str
    type: str
    category: str
    timestamp: str
    organization_id: str | None = None
    workspace_id: str | None = None
    project_id: str | None = None
    session_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None
    correlation_id: str | None = None
    causation_id: str | None = None
    classification: str
    payload: dict[str, Any]


def to_envelope(event: BaseEvent, sequence: int) -> TelemetryEnvelope:
    """Build a :class:`TelemetryEnvelope` from an event and a broadcast sequence.

    Args:
        event: The enterprise event to wrap.
        sequence: The monotonic broadcast-order key for this delivery.

    Returns:
        The immutable wire envelope for the event.
    """
    return TelemetryEnvelope(
        sequence=sequence,
        event_id=event.event_id,
        type=event.event_type,
        category=event.event_category.value,
        timestamp=event.timestamp.isoformat(),
        organization_id=event.organization_id,
        workspace_id=event.workspace_id,
        project_id=event.project_id,
        session_id=event.session_id,
        task_id=event.task_id,
        agent_id=event.agent_id,
        correlation_id=event.correlation_id,
        causation_id=event.causation_id,
        classification=event.security_classification.value,
        payload=dict(event.payload),
    )
