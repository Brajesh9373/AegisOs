"""JSON serialization helpers (SECTION 96)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from ecms.shared.exceptions import SerializationError

__all__ = ["from_json", "model_to_dict", "to_json"]


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    message = f"Object of type {type(value).__name__} is not JSON serializable"
    raise TypeError(message)


def to_json(value: object) -> str:
    """Serialize a value (including Pydantic models) to a JSON string.

    Args:
        value: The value to serialize.

    Returns:
        A JSON string.

    Raises:
        SerializationError: If the value cannot be serialized.
    """
    try:
        if isinstance(value, BaseModel):
            return value.model_dump_json()
        return json.dumps(value, default=_json_default, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise SerializationError(f"could not serialize value to JSON: {exc}") from exc


def from_json(payload: str) -> Any:
    """Deserialize a JSON string into Python objects.

    Args:
        payload: A JSON string.

    Returns:
        The decoded Python object.

    Raises:
        SerializationError: If the payload is not valid JSON.
    """
    try:
        return json.loads(payload)
    except (TypeError, ValueError) as exc:
        raise SerializationError(f"could not parse JSON: {exc}") from exc


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    """Return a JSON-compatible dictionary for a Pydantic model."""
    return model.model_dump(mode="json")
