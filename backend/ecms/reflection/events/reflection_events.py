"""Reflection event factories (SECTION 62).

Reflection publishes events as it analyzes a task and proposes learning; it never
modifies the graph directly.
"""

from __future__ import annotations

from typing import Any

from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent, make_event

__all__ = [
    "candidate_generated",
    "improvement_suggested",
    "pattern_discovered",
    "reflection_completed",
    "reflection_started",
]

_PRODUCER = "reflection-engine"


def _event(event_type: str, payload: dict[str, Any]) -> BaseEvent:
    return make_event(event_type, EventCategory.REFLECTION, _PRODUCER, payload=payload)


def reflection_started(task_id: str) -> BaseEvent:
    """Emitted when reflection begins for a task (SECTION 62)."""
    return _event("ReflectionStarted", {"task_id": task_id})


def reflection_completed(reflection_id: str) -> BaseEvent:
    """Emitted when reflection completes (SECTION 62)."""
    return _event("ReflectionCompleted", {"reflection_id": reflection_id})


def pattern_discovered(reflection_id: str, pattern: str) -> BaseEvent:
    """Emitted when reflection discovers a reusable pattern (SECTION 62)."""
    return _event("PatternDiscovered", {"reflection_id": reflection_id, "pattern": pattern})


def improvement_suggested(reflection_id: str, improvement: str) -> BaseEvent:
    """Emitted when reflection suggests an improvement (SECTION 62)."""
    return _event(
        "ImprovementSuggested",
        {"reflection_id": reflection_id, "improvement": improvement},
    )


def candidate_generated(candidate_id: str) -> BaseEvent:
    """Emitted when reflection generates a knowledge candidate (SECTION 62)."""
    return _event("KnowledgeCandidateGenerated", {"candidate_id": candidate_id})
