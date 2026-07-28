"""Knowledge event factories (SECTION 57).

Every stage of the knowledge pipeline emits an immutable event in the KNOWLEDGE
category, populated from the ambient request context so the whole pipeline is
traceable and replayable.
"""

from __future__ import annotations

from typing import Any

from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent, make_event

__all__ = [
    "knowledge_discovered",
    "knowledge_merged",
    "knowledge_normalized",
    "knowledge_rejected",
    "knowledge_validated",
    "knowledge_version_created",
]

_PRODUCER = "knowledge-engine"


def _event(event_type: str, payload: dict[str, Any]) -> BaseEvent:
    return make_event(event_type, EventCategory.KNOWLEDGE, _PRODUCER, payload=payload)


def knowledge_discovered(uko_id: str) -> BaseEvent:
    """Emitted when a UKO enters the knowledge pipeline (SECTION 57)."""
    return _event("KnowledgeDiscovered", {"uko_id": uko_id})


def knowledge_normalized(uko_id: str) -> BaseEvent:
    """Emitted after a UKO has been normalized (SECTION 57)."""
    return _event("KnowledgeNormalized", {"uko_id": uko_id})


def knowledge_validated(uco_id: str) -> BaseEvent:
    """Emitted when a generated cognitive object passes validation (SECTION 57)."""
    return _event("KnowledgeValidated", {"uco_id": uco_id})


def knowledge_rejected(uco_id: str, reason: str) -> BaseEvent:
    """Emitted when a generated cognitive object fails validation (SECTION 57)."""
    return _event("KnowledgeRejected", {"uco_id": uco_id, "reason": reason})


def knowledge_version_created(uco_id: str, *, version: int) -> BaseEvent:
    """Emitted when a new version of a cognitive object is created (SECTION 57)."""
    return _event("KnowledgeVersionCreated", {"uco_id": uco_id, "version": version})


def knowledge_merged(uco_id: str, sources: list[str]) -> BaseEvent:
    """Emitted when duplicate cognitive objects are merged (SECTION 57)."""
    return _event("KnowledgeMerged", {"uco_id": uco_id, "sources": sources})
