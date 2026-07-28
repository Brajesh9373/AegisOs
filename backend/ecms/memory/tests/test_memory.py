"""Tests for the default memory engine (SECTION 77/157/158)."""

from __future__ import annotations

from ecms.events import InMemoryEventBus
from ecms.infrastructure.reasoning import DeterministicEmbeddingProvider
from ecms.knowledge.infrastructure.repository import InMemoryKnowledgeRepository
from ecms.memory import DefaultMemoryEngine
from ecms.shared.enums import EventCategory, MemoryStatus
from ecms.shared.events import BaseEvent
from ecms.shared.models import UniversalCognitiveObject


def _uco(
    name: str,
    ontology_type: str = "component",
    *,
    importance: int = 50,
    confidence: int = 50,
) -> UniversalCognitiveObject:
    return UniversalCognitiveObject(
        canonical_name=name,
        display_name=name,
        ontology_type=ontology_type,
        description=f"{name} description",
        importance=importance,
        confidence=confidence,
    )


async def _repository() -> InMemoryKnowledgeRepository:
    repository = InMemoryKnowledgeRepository(DeterministicEmbeddingProvider())
    await repository.add(_uco("AuthService", "security_component", importance=90))
    await repository.add(_uco("Widget", "component", importance=10))
    await repository.add(_uco("PaymentService", "service", importance=70))
    return repository


async def test_activate_builds_bounded_working_memory() -> None:
    engine = DefaultMemoryEngine(await _repository())
    working = await engine.activate("AuthService", task_id="task-1", activation_limit=2)
    assert working.task_id == "task-1"
    assert len(working.active_uco_references) <= 2
    assert working.activation_budget == 2


async def test_retrieve_uses_semantic_cache() -> None:
    engine = DefaultMemoryEngine(await _repository())
    first = await engine.retrieve("PaymentService", limit=3)
    second = await engine.retrieve("PaymentService", limit=3)
    assert [uco.uco_id for uco in first] == [uco.uco_id for uco in second]
    assert engine.statistics()["cache"]["hits"] >= 1


async def test_scope_restricts_activation() -> None:
    repository = await _repository()
    engine = DefaultMemoryEngine(repository)
    everything = await repository.all()
    allowed = next(uco for uco in everything if uco.display_name == "Widget")
    working = await engine.activate("anything", task_id="task-1", scope=[allowed.uco_id])
    assert working.active_uco_references == [allowed.uco_id]


async def test_release_marks_and_evicts() -> None:
    engine = DefaultMemoryEngine(await _repository())
    working = await engine.activate("AuthService", task_id="task-1")
    released = await engine.release(working)
    assert released.status is MemoryStatus.RELEASED
    assert released.expires_at is not None


async def test_activation_emits_events() -> None:
    bus = InMemoryEventBus()
    seen: list[str] = []

    async def handler(event: BaseEvent) -> None:
        seen.append(event.event_type)

    bus.subscribe(handler, category=EventCategory.MEMORY)
    engine = DefaultMemoryEngine(await _repository(), event_bus=bus)
    working = await engine.activate("AuthService", task_id="task-1")
    await engine.release(working)
    assert "WorkingMemoryCreated" in seen
    assert "WorkingMemoryActivated" in seen
    assert "WorkingMemoryReleased" in seen


async def test_compress_returns_summary() -> None:
    engine = DefaultMemoryEngine(await _repository())
    summary = await engine.compress("a long execution transcript to compress")
    assert isinstance(summary, str)
    assert summary
