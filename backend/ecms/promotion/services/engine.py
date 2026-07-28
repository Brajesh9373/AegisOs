"""Default knowledge promotion engine (SECTION 34/79/103/165).

The promotion pipeline is the sole path that modifies enterprise knowledge:
validate a candidate, detect duplicates, evaluate confidence and policy, apply an
optional human-approval gate, then promote it into a cognitive object indexed in
the knowledge store and projected into the graph. No agent writes knowledge
directly.
"""

from __future__ import annotations

from ecms.events import EventBus
from ecms.graph import GraphEngine
from ecms.knowledge.interfaces.engine import KnowledgeRepository
from ecms.promotion.events.promotion_events import (
    candidate_rejected,
    candidate_validated,
    knowledge_merged,
    knowledge_promoted,
)
from ecms.shared.enums import ApprovalStatus, PromotionStatus, ValidationStatus
from ecms.shared.events import BaseEvent
from ecms.shared.models import (
    Evidence,
    KnowledgeCandidate,
    UniversalCognitiveObject,
)

__all__ = ["DefaultPromotionEngine"]


class DefaultPromotionEngine:
    """Validates and promotes candidates into enterprise knowledge (SECTION 79)."""

    def __init__(
        self,
        *,
        graph: GraphEngine | None = None,
        knowledge: KnowledgeRepository | None = None,
        event_bus: EventBus | None = None,
        min_confidence: int = 50,
        auto_approve_threshold: int = 70,
    ) -> None:
        """Initialize with graph/knowledge sinks and confidence policy thresholds."""
        self._graph = graph
        self._knowledge = knowledge
        self._event_bus = event_bus
        self._min_confidence = min_confidence
        self._auto_approve_threshold = auto_approve_threshold
        self._processed = 0
        self._promoted = 0
        self._rejected = 0
        self._merged = 0
        self._pending = 0

    async def promote(self, candidates: list[KnowledgeCandidate]) -> list[UniversalCognitiveObject]:
        """Run the promotion pipeline for each candidate (SECTION 103)."""
        promoted: list[UniversalCognitiveObject] = []
        for candidate in candidates:
            self._processed += 1
            if self.validate(candidate) is not ValidationStatus.VALIDATED:
                candidate.validation_status = ValidationStatus.REJECTED
                candidate.promotion_status = PromotionStatus.REJECTED
                self._rejected += 1
                await self._emit(candidate_rejected(candidate.candidate_id, "validation"))
                continue
            candidate.validation_status = ValidationStatus.VALIDATED
            await self._emit(candidate_validated(candidate.candidate_id))
            if await self._is_duplicate(candidate):
                candidate.promotion_status = PromotionStatus.MERGED
                self._merged += 1
                await self._emit(knowledge_merged(candidate.candidate_id))
                continue
            if candidate.confidence < self._auto_approve_threshold:
                candidate.approval_status = ApprovalStatus.PENDING
                self._pending += 1
                continue
            candidate.approval_status = ApprovalStatus.AUTO_APPROVED
            uco = self._to_uco(candidate)
            if self._knowledge is not None:
                await self._knowledge.add(uco)
            if self._graph is not None:
                await self._graph.upsert_uco(uco)
            candidate.promotion_status = PromotionStatus.PROMOTED
            self._promoted += 1
            promoted.append(uco)
            await self._emit(knowledge_promoted(uco.uco_id))
        return promoted

    def validate(self, candidate: KnowledgeCandidate) -> ValidationStatus:
        """Validate a candidate against confidence and content policy (SECTION 103)."""
        if candidate.proposed_uco and candidate.confidence >= self._min_confidence:
            return ValidationStatus.VALIDATED
        return ValidationStatus.REJECTED

    def statistics(self) -> dict[str, int]:
        """Return promotion counters (SECTION 79)."""
        return {
            "processed": self._processed,
            "promoted": self._promoted,
            "rejected": self._rejected,
            "merged": self._merged,
            "pending": self._pending,
        }

    async def _is_duplicate(self, candidate: KnowledgeCandidate) -> bool:
        if self._knowledge is None:
            return False
        proposed = candidate.proposed_uco or {}
        canonical_name = proposed.get("canonical_name")
        existing = await self._knowledge.all()
        return any(uco.canonical_name == canonical_name for uco in existing)

    @staticmethod
    def _to_uco(candidate: KnowledgeCandidate) -> UniversalCognitiveObject:
        proposed = candidate.proposed_uco or {}
        canonical_name = str(proposed.get("canonical_name", candidate.candidate_id))
        return UniversalCognitiveObject(
            canonical_name=canonical_name,
            display_name=str(proposed.get("display_name", canonical_name)),
            ontology_type=str(proposed.get("ontology_type", "pattern")),
            description=str(proposed.get("description", "")),
            confidence=candidate.confidence,
            importance=candidate.importance,
            evidence=[Evidence(uko_id=reference) for reference in candidate.supporting_evidence],
            knowledge_sources=list(candidate.supporting_evidence),
        )

    async def _emit(self, event: BaseEvent) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)
