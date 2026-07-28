"""Reflection and knowledge-candidate domain models (SECTION 44/45).

Reflection captures the lessons of a completed task and proposes learning as
:class:`KnowledgeCandidate` objects. Candidates remain isolated from enterprise
knowledge until the Promotion pipeline validates and promotes them.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ecms.shared.enums import ApprovalStatus, PromotionStatus, ValidationStatus
from ecms.shared.ids import new_id
from ecms.shared.models.base import DomainModel
from ecms.shared.time import utcnow

__all__ = ["KnowledgeCandidate", "Reflection"]


def _reflection_id() -> str:
    return new_id("refl")


def _candidate_id() -> str:
    return new_id("cand")


class Reflection(DomainModel):
    """Lessons captured after task execution; never modifies knowledge (SECTION 45)."""

    reflection_id: str = Field(default_factory=_reflection_id)
    task_id: str
    summary: str
    mistakes: list[str] = Field(default_factory=list)
    successes: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    knowledge_candidates: list[str] = Field(default_factory=list)
    confidence: int = Field(default=0, ge=0, le=100)
    generated_at: datetime = Field(default_factory=utcnow)


class KnowledgeCandidate(DomainModel):
    """Proposed organizational learning awaiting promotion (SECTION 44).

    A candidate is not part of enterprise knowledge until promoted; it carries its
    own validation, approval and promotion status through the promotion pipeline.
    """

    candidate_id: str = Field(default_factory=_candidate_id)
    source_task: str | None = None
    source_session: str | None = None
    reflection_id: str | None = None
    confidence: int = Field(default=0, ge=0, le=100)
    importance: int = Field(default=0, ge=0, le=100)
    proposed_uco: dict[str, Any] | None = None
    supporting_evidence: list[str] = Field(default_factory=list)
    graph_changes: list[dict[str, Any]] = Field(default_factory=list)
    duplicate_candidates: list[str] = Field(default_factory=list)
    validation_status: ValidationStatus = ValidationStatus.NEEDS_REVIEW
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    promotion_status: PromotionStatus = PromotionStatus.PENDING
    created_at: datetime = Field(default_factory=utcnow)
