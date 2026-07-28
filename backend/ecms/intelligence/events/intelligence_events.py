"""Intelligence event factories (SECTION 60).

The planner emits events as it converts intent into an execution plan.
"""

from __future__ import annotations

from typing import Any

from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent, make_event

__all__ = ["planner_completed", "planner_started"]

_PRODUCER = "intelligence-layer"


def _event(event_type: str, payload: dict[str, Any]) -> BaseEvent:
    return make_event(event_type, EventCategory.RUNTIME, _PRODUCER, payload=payload)


def planner_started(task_id: str) -> BaseEvent:
    """Emitted when planning begins (SECTION 60)."""
    return _event("PlannerStarted", {"task_id": task_id})


def planner_completed(task_id: str, plan_id: str) -> BaseEvent:
    """Emitted when planning completes (SECTION 60)."""
    return _event("PlannerCompleted", {"task_id": task_id, "plan_id": plan_id})
