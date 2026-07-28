"""Memory event factories (SECTION 59).

Memory lifecycle transitions emit immutable events in the MEMORY category so the
activation and release of knowledge is fully observable and replayable.
"""

from __future__ import annotations

from typing import Any

from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent, make_event

__all__ = [
    "memory_promotion_completed",
    "memory_promotion_started",
    "session_memory_updated",
    "working_memory_activated",
    "working_memory_created",
    "working_memory_released",
]

_PRODUCER = "memory-engine"


def _event(event_type: str, payload: dict[str, Any]) -> BaseEvent:
    return make_event(event_type, EventCategory.MEMORY, _PRODUCER, payload=payload)


def working_memory_created(working_memory_id: str) -> BaseEvent:
    """Emitted when a working memory is created (SECTION 59)."""
    return _event("WorkingMemoryCreated", {"working_memory_id": working_memory_id})


def working_memory_activated(working_memory_id: str, count: int) -> BaseEvent:
    """Emitted when knowledge is activated into a working memory (SECTION 59)."""
    return _event(
        "WorkingMemoryActivated",
        {"working_memory_id": working_memory_id, "activated": count},
    )


def working_memory_released(working_memory_id: str) -> BaseEvent:
    """Emitted when a working memory is released after task completion (SECTION 59)."""
    return _event("WorkingMemoryReleased", {"working_memory_id": working_memory_id})


def session_memory_updated(session_memory_id: str) -> BaseEvent:
    """Emitted when session memory accumulates new understanding (SECTION 59)."""
    return _event("SessionMemoryUpdated", {"session_memory_id": session_memory_id})


def memory_promotion_started(session_memory_id: str) -> BaseEvent:
    """Emitted when session memory begins promotion to knowledge (SECTION 59)."""
    return _event("MemoryPromotionStarted", {"session_memory_id": session_memory_id})


def memory_promotion_completed(session_memory_id: str, candidates: int) -> BaseEvent:
    """Emitted when session-memory promotion completes (SECTION 59)."""
    return _event(
        "MemoryPromotionCompleted",
        {"session_memory_id": session_memory_id, "candidates": candidates},
    )
