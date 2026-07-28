"""Tool event factories (SECTION 61).

Every tool invocation publishes events so execution is auditable and replayable.
"""

from __future__ import annotations

from typing import Any

from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent, make_event

__all__ = [
    "tool_artifact_generated",
    "tool_execution_completed",
    "tool_execution_failed",
    "tool_execution_started",
    "tool_permission_denied",
]

_PRODUCER = "tool-runtime"


def _event(event_type: str, payload: dict[str, Any]) -> BaseEvent:
    return make_event(event_type, EventCategory.TOOL, _PRODUCER, payload=payload)


def tool_execution_started(execution_id: str, tool_name: str) -> BaseEvent:
    """Emitted when a tool invocation starts (SECTION 61)."""
    return _event(
        "ToolExecutionStarted",
        {"execution_id": execution_id, "tool": tool_name},
    )


def tool_execution_completed(execution_id: str, tool_name: str) -> BaseEvent:
    """Emitted when a tool invocation completes successfully (SECTION 61)."""
    return _event(
        "ToolExecutionCompleted",
        {"execution_id": execution_id, "tool": tool_name},
    )


def tool_execution_failed(execution_id: str, tool_name: str, error: str) -> BaseEvent:
    """Emitted when a tool invocation fails (SECTION 61)."""
    return _event(
        "ToolExecutionFailed",
        {"execution_id": execution_id, "tool": tool_name, "error": error},
    )


def tool_permission_denied(tool_name: str) -> BaseEvent:
    """Emitted when a tool invocation is denied by the permission engine (SECTION 61)."""
    return _event("ToolPermissionDenied", {"tool": tool_name})


def tool_artifact_generated(execution_id: str, artifact: str) -> BaseEvent:
    """Emitted when a tool invocation generates an artifact (SECTION 61)."""
    return _event(
        "ToolArtifactGenerated",
        {"execution_id": execution_id, "artifact": artifact},
    )
