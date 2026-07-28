"""Tests for the default knowledge promotion engine (SECTION 79/103)."""

from __future__ import annotations

from ecms.events import InMemoryEventBus
from ecms.graph import GraphEngine
from ecms.infrastructure.reasoning import DeterministicEmbeddingProvider
from ecms.knowledge.infrastructure.repository import InMemoryKnowledgeRepository
from ecms.promotion import DefaultPromotionEngine
from ecms.shared.enums import EventCategory, PromotionStatus
from ecms.shared.events import BaseEvent
from ecms.shared.models import KnowledgeCandidate


def _candidate(name: str = "AuthPattern", *, confidence: int = 90) -> KnowledgeCandidate:
    return KnowledgeCandidate(
        source_task="task-1",
        confidence=confidence,
        importance=60,
        proposed_uco={
            "canonical_name": name,
            "ontology_type": "pattern",
            "description": f"{name} pattern",
        },
        supporting_evidence=["uco-1"],
    )


async def test_promote_high_confidence_candidate() -> None:
    graph = GraphEngine()
    knowledge = InMemoryKnowledgeRepository(DeterministicEmbeddingProvider())
    engine = DefaultPromotionEngine(graph=graph, knowledge=knowledge)
    candidate = _candidate()
    promoted = await engine.promote([candidate])
    assert len(promoted) == 1
    assert candidate.promotion_status is PromotionStatus.PROMOTED
    assert await knowledge.get(promoted[0].uco_id) is not None
    assert await graph.find_node(promoted[0].uco_id) is not None
    assert engine.statistics()["promoted"] == 1


async def test_reject_low_confidence_candidate() -> None:
    engine = DefaultPromotionEngine(min_confidence=50)
    candidate = _candidate(confidence=20)
    promoted = await engine.promote([candidate])
    assert promoted == []
    assert candidate.promotion_status is PromotionStatus.REJECTED
    assert engine.statistics()["rejected"] == 1


async def test_candidate_below_auto_approve_stays_pending() -> None:
    engine = DefaultPromotionEngine(min_confidence=50, auto_approve_threshold=80)
    candidate = _candidate(confidence=60)
    promoted = await engine.promote([candidate])
    assert promoted == []
    assert engine.statistics()["pending"] == 1


async def test_duplicate_candidate_is_merged() -> None:
    knowledge = InMemoryKnowledgeRepository(DeterministicEmbeddingProvider())
    engine = DefaultPromotionEngine(knowledge=knowledge)
    await engine.promote([_candidate("Dup")])
    engine_again = DefaultPromotionEngine(knowledge=knowledge)
    candidate = _candidate("Dup")
    await engine_again.promote([candidate])
    assert candidate.promotion_status is PromotionStatus.MERGED
    assert engine_again.statistics()["merged"] == 1


async def test_promotion_emits_events() -> None:
    bus = InMemoryEventBus()
    seen: list[str] = []

    async def handler(event: BaseEvent) -> None:
        seen.append(event.event_type)

    bus.subscribe(handler, category=EventCategory.KNOWLEDGE)
    engine = DefaultPromotionEngine(event_bus=bus)
    await engine.promote([_candidate()])
    assert "KnowledgeCandidateValidated" in seen
    assert "KnowledgePromoted" in seen
