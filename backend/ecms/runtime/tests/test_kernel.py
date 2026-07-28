"""Tests for the runtime kernel execution pipeline (SECTION 71/92)."""

from __future__ import annotations

from ecms.events import InMemoryEventBus
from ecms.graph import GraphEngine
from ecms.infrastructure.reasoning import DeterministicEmbeddingProvider
from ecms.knowledge.infrastructure.repository import InMemoryKnowledgeRepository
from ecms.memory import DefaultMemoryEngine
from ecms.runtime import RuntimeKernel
from ecms.shared.enums import StrategyType, TaskStatus
from ecms.shared.models import (
    ExecutionPlan,
    KnowledgeCandidate,
    Reflection,
    Task,
    ToolExecution,
    UniversalCognitiveObject,
    WorkingMemory,
)


def _uco(name: str, ontology_type: str = "component") -> UniversalCognitiveObject:
    return UniversalCognitiveObject(
        canonical_name=name,
        display_name=name,
        ontology_type=ontology_type,
        description=f"{name} description",
        importance=70,
    )


async def _kernel(*, event_bus: InMemoryEventBus | None = None, **kwargs: object) -> RuntimeKernel:
    repository = InMemoryKnowledgeRepository(DeterministicEmbeddingProvider())
    await repository.add(_uco("AuthService", "security_component"))
    await repository.add(_uco("PaymentService", "service"))
    memory = DefaultMemoryEngine(repository, event_bus=event_bus)
    return RuntimeKernel(
        knowledge=repository,
        memory=memory,
        graph=GraphEngine(event_bus=event_bus),
        event_bus=event_bus,
        **kwargs,  # type: ignore[arg-type]
    )


async def test_execute_runs_core_pipeline() -> None:
    kernel = await _kernel()
    result = await kernel.execute("AuthService", organization_id="org-1", user_id="user-1")
    assert result.status == "completed"
    assert result.activated_uco_ids
    assert result.graph_nodes
    assert result.agent_id is not None
    task = kernel.tasks.get(result.task_id)
    assert task is not None
    assert task.status is TaskStatus.COMPLETED


async def test_execute_emits_pipeline_events() -> None:
    bus = InMemoryEventBus()
    seen: list[str] = []

    async def handler(event: object) -> None:
        seen.append(getattr(event, "event_type", ""))

    bus.subscribe(handler)
    kernel = await _kernel(event_bus=bus)
    await kernel.execute("AuthService", organization_id="org-1", user_id="user-1")
    for event_type in (
        "PromptReceived",
        "TaskCreated",
        "TaskStarted",
        "AgentCreated",
        "WorkingMemoryCreated",
        "NodeCreated",
        "TaskCompleted",
    ):
        assert event_type in seen


class _FakePlanner:
    async def plan(self, task: Task, context: str) -> ExecutionPlan:
        return ExecutionPlan(task_id=task.task_id, strategy=StrategyType.SEQUENTIAL)


class _FakeToolRunner:
    async def run(self, task: Task, working_memory: WorkingMemory) -> list[ToolExecution]:
        return [ToolExecution(tool_name="filesystem.read", task_id=task.task_id)]


class _FakeReflector:
    async def reflect(self, task: Task, activated: list[UniversalCognitiveObject]) -> Reflection:
        return Reflection(task_id=task.task_id, summary="looks good")

    async def generate_candidates(
        self,
        task: Task,
        reflection: Reflection,
        activated: list[UniversalCognitiveObject],
    ) -> list[KnowledgeCandidate]:
        return [
            KnowledgeCandidate(
                source_task=task.task_id,
                confidence=75,
                proposed_uco={"canonical_name": "Pattern"},
            )
        ]


class _FakePromoter:
    async def promote(self, candidates: list[KnowledgeCandidate]) -> list[UniversalCognitiveObject]:
        return [
            UniversalCognitiveObject(
                canonical_name="Promoted",
                display_name="Promoted",
                ontology_type="pattern",
                description="promoted knowledge",
            )
            for _ in candidates
        ]


async def test_execute_runs_full_pipeline_with_collaborators() -> None:
    kernel = await _kernel(
        planner=_FakePlanner(),
        tool_runner=_FakeToolRunner(),
        reflector=_FakeReflector(),
        promoter=_FakePromoter(),
    )
    result = await kernel.execute("PaymentService", organization_id="org-1", user_id="user-1")
    assert result.plan_id is not None
    assert result.tool_executions
    assert result.reflection_id is not None
    assert result.knowledge_candidates


async def test_execute_reuses_existing_session() -> None:
    kernel = await _kernel()
    first = await kernel.execute("AuthService", organization_id="org-1", user_id="user-1")
    second = await kernel.execute(
        "PaymentService",
        organization_id="org-1",
        user_id="user-1",
        session_id=first.session_id,
    )
    assert second.session_id == first.session_id
