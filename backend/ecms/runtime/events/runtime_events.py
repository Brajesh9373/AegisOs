"""Runtime event factories: task, session and agent events (SECTION 55/56/60).

The runtime kernel emits an immutable event at every lifecycle transition so the
whole execution is observable, auditable and replayable.
"""

from __future__ import annotations

from typing import Any

from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent, make_event

__all__ = [
    "agent_assigned",
    "agent_created",
    "prompt_received",
    "session_completed",
    "session_created",
    "session_started",
    "task_cancelled",
    "task_completed",
    "task_created",
    "task_failed",
    "task_started",
]

_PRODUCER = "runtime-kernel"


def _event(event_type: str, category: EventCategory, payload: dict[str, Any]) -> BaseEvent:
    return make_event(event_type, category, _PRODUCER, payload=payload)


def prompt_received(task_id: str, prompt: str) -> BaseEvent:
    """Emitted when a prompt enters the runtime (SECTION 93)."""
    return _event("PromptReceived", EventCategory.RUNTIME, {"task_id": task_id, "prompt": prompt})


def task_created(task_id: str) -> BaseEvent:
    """Emitted when a task is created (SECTION 55)."""
    return _event("TaskCreated", EventCategory.TASK, {"task_id": task_id})


def task_started(task_id: str) -> BaseEvent:
    """Emitted when a task starts executing (SECTION 55)."""
    return _event("TaskStarted", EventCategory.TASK, {"task_id": task_id})


def task_completed(task_id: str) -> BaseEvent:
    """Emitted when a task completes successfully (SECTION 55)."""
    return _event("TaskCompleted", EventCategory.TASK, {"task_id": task_id})


def task_failed(task_id: str, error: str) -> BaseEvent:
    """Emitted when a task fails (SECTION 55)."""
    return _event("TaskFailed", EventCategory.TASK, {"task_id": task_id, "error": error})


def task_cancelled(task_id: str) -> BaseEvent:
    """Emitted when a task is cancelled (SECTION 55)."""
    return _event("TaskCancelled", EventCategory.TASK, {"task_id": task_id})


def session_created(session_id: str) -> BaseEvent:
    """Emitted when a session is created (SECTION 56)."""
    return _event("SessionCreated", EventCategory.SESSION, {"session_id": session_id})


def session_started(session_id: str) -> BaseEvent:
    """Emitted when a session starts (SECTION 56)."""
    return _event("SessionStarted", EventCategory.SESSION, {"session_id": session_id})


def session_completed(session_id: str) -> BaseEvent:
    """Emitted when a session completes (SECTION 56)."""
    return _event("SessionCompleted", EventCategory.SESSION, {"session_id": session_id})


def agent_created(agent_id: str) -> BaseEvent:
    """Emitted when an agent is created (SECTION 60)."""
    return _event("AgentCreated", EventCategory.RUNTIME, {"agent_id": agent_id})


def agent_assigned(agent_id: str, task_id: str) -> BaseEvent:
    """Emitted when an agent is assigned to a task (SECTION 60/98)."""
    return _event(
        "AgentAssigned",
        EventCategory.RUNTIME,
        {"agent_id": agent_id, "task_id": task_id},
    )
