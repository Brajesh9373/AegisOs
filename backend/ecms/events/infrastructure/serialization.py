"""Event serialization and deserialization (SECTION 99)."""

from __future__ import annotations

from ecms.shared.events import BaseEvent
from ecms.shared.exceptions import SerializationError

__all__ = ["deserialize_event", "serialize_event"]


def serialize_event(event: BaseEvent) -> str:
    """Serialize an event to a JSON string."""
    return event.model_dump_json()


def deserialize_event(payload: str) -> BaseEvent:
    """Deserialize a JSON string into a :class:`BaseEvent`.

    Raises:
        SerializationError: If the payload is not a valid event.
    """
    try:
        return BaseEvent.model_validate_json(payload)
    except ValueError as exc:
        raise SerializationError(f"could not deserialize event: {exc}") from exc
