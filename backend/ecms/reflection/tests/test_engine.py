"""Tests for the default reflection engine (SECTION 78/101/102)."""

from __future__ import annotations

from ecms.events import InMemoryEventBus
from ecms.reflection import DefaultReflectionEngine
from ecms.shared.enums import EventCategory, TaskStatus
from ecms.shared.events import BaseEvent
from ecms.shared.models import Task, UniversalCognitiveObject


def _task(*, status: TaskStatus = TaskStatus.COMPLETED, errors: list[str] | None = None) -> Task:
    return Task(
        session_id="s",
        organization_id="o",
        user_id="u",
        title="build auth",
        goal="implement JWT authentication",
        status=status,
        errors=errors or [],
    )


def _uco(name: str, ontology_type: str) -> UniversalCognitiveObject:
    return UniversalCognitiveObject(
        canonical_name=name,
        display_name=name,
        ontology_type=ontology_type,
        description=f"{name} description",
    )


async def test_reflect_on_successful_task() -> None:
    engine = DefaultReflectionEngine()
    activated = [_uco("AuthService", "security_component"), _uco("Jwt", "security_component")]
    reflection = await engine.reflect(_task(), activated)
    assert reflection.successes
    assert reflection.confidence == 90
    assert "reuse of security_component knowledge" in reflection.patterns
    assert reflection.summary


async def test_reflect_on_failed_task_records_mistakes() -> None:
    engine = DefaultReflectionEngine()
    reflection = await engine.reflect(_task(status=TaskStatus.FAILED, errors=["boom"]), [])
    assert reflection.mistakes == ["boom"]
    assert reflection.confidence == 40
    assert reflection.successes == []
    assert "capture knowledge for this task domain" in reflection.improvements


async def test_generate_candidates_from_reflection() -> None:
    engine = DefaultReflectionEngine()
    activated = [_uco("AuthService", "security_component")]
    task = _task()
    reflection = await engine.reflect(task, activated)
    candidates = await engine.generate_candidates(task, reflection, activated)
    assert candidates
    assert candidates[0].source_task == task.task_id
    assert candidates[0].supporting_evidence == [activated[0].uco_id]
    assert reflection.knowledge_candidates == [c.candidate_id for c in candidates]


async def test_reflection_emits_events() -> None:
    bus = InMemoryEventBus()
    seen: list[str] = []

    async def handler(event: BaseEvent) -> None:
        seen.append(event.event_type)

    bus.subscribe(handler, category=EventCategory.REFLECTION)
    engine = DefaultReflectionEngine(event_bus=bus)
    activated = [_uco("AuthService", "security_component")]
    task = _task()
    reflection = await engine.reflect(task, activated)
    await engine.generate_candidates(task, reflection, activated)
    assert "ReflectionStarted" in seen
    assert "ReflectionCompleted" in seen
    assert "PatternDiscovered" in seen
    assert "KnowledgeCandidateGenerated" in seen
