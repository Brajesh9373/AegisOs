"""Knowledge promotion event factories (SECTION 57/103).

Promotion is the only path that modifies enterprise knowledge; every decision it
makes is announced as a KNOWLEDGE event.
"""

from __future__ import annotations

from typing import Any

from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent, make_event

__all__ = [
    "candidate_rejected",
    "candidate_validated",
    "knowledge_merged",
    "knowledge_promoted",
]

_PRODUCER = "promotion-engine"


def _event(event_type: str, payload: dict[str, Any]) -> BaseEvent:
    return make_event(event_type, EventCategory.KNOWLEDGE, _PRODUCER, payload=payload)


def candidate_validated(candidate_id: str) -> BaseEvent:
    """Emitted when a candidate passes validation (SECTION 57)."""
    return _event("KnowledgeCandidateValidated", {"candidate_id": candidate_id})


def candidate_rejected(candidate_id: str, reason: str) -> BaseEvent:
    """Emitted when a candidate is rejected (SECTION 57)."""
    return _event(
        "KnowledgeCandidateRejected",
        {"candidate_id": candidate_id, "reason": reason},
    )


def knowledge_promoted(uco_id: str) -> BaseEvent:
    """Emitted when a candidate is promoted into enterprise knowledge (SECTION 57)."""
    return _event("KnowledgePromoted", {"uco_id": uco_id})


def knowledge_merged(candidate_id: str) -> BaseEvent:
    """Emitted when a candidate is merged into existing knowledge (SECTION 57)."""
    return _event("KnowledgeMerged", {"candidate_id": candidate_id})
