"""Unit tests for backend domain models and extensions (Part 3 + SECTION 40-49/110/284-288)."""

from __future__ import annotations

from ecms.shared.enums import (
    AgentRole,
    ApprovalStatus,
    EventCategory,
    OntologyCategory,
    RelationshipType,
    StrategyType,
    ToolExecutionStatus,
)
from ecms.shared.events import BaseEvent
from ecms.shared.models import (
    Agent,
    Artifact,
    Decision,
    Episode,
    Evidence,
    ExecutionPlan,
    Goal,
    KnowledgeCandidate,
    KnowledgeMemory,
    Reflection,
    Relationship,
    RuntimeContext,
    Task,
    ToolExecution,
    WorkingMemory,
)


def test_agent_defaults() -> None:
    agent = Agent(role=AgentRole.PLANNER)
    assert agent.agent_id.startswith("agent-")
    assert agent.status.value == "created"
    assert agent.token_budget.remaining is None
    assert agent.temperature == 0.0


def test_runtime_context_and_tool_execution() -> None:
    context = RuntimeContext(agent_id="agent-1")
    assert context.runtime_context_id.startswith("rtx-")
    execution = ToolExecution(tool_name="filesystem.read")
    assert execution.execution_id.startswith("texec-")
    assert execution.status is ToolExecutionStatus.PENDING


def test_planning_models() -> None:
    goal = Goal(description="ship login")
    assert goal.goal_id.startswith("goal-")
    plan = ExecutionPlan(task_id="task-1", strategy=StrategyType.PARALLEL)
    assert plan.version == 1
    decision = Decision(question="which db?", chosen="postgres", rationale="acid")
    assert decision.decision_id.startswith("dec-")


def test_artifact_provenance() -> None:
    artifact = Artifact(artifact_type="execution_plan", name="plan-v1", origin_task="task-1")
    assert artifact.artifact_id.startswith("art-")
    assert artifact.version == 1


def test_reflection_and_candidate() -> None:
    reflection = Reflection(task_id="task-1", summary="went well")
    assert reflection.reflection_id.startswith("refl-")
    candidate = KnowledgeCandidate(source_task="task-1", confidence=80)
    assert candidate.candidate_id.startswith("cand-")
    assert candidate.approval_status is ApprovalStatus.PENDING


def test_new_enums_present() -> None:
    assert RelationshipType.DEPENDS_ON.value == "depends_on"
    assert OntologyCategory.SECURITY.value == "security"
    assert EventCategory.TASK.value == "task"
    assert EventCategory.REFLECTION.value == "reflection"


def test_task_hierarchy_and_reflection_fields() -> None:
    task = Task(
        session_id="s",
        organization_id="o",
        user_id="u",
        title="t",
        goal="g",
        parent_task="task-parent",
    )
    assert task.parent_task == "task-parent"
    assert task.child_tasks == []
    assert task.planner_output is None
    assert task.reflection_id is None


def test_evidence_and_relationship_extensions() -> None:
    evidence = Evidence(uko_id="uko-1", source="git", checksum="abc")
    assert evidence.source == "git"
    assert evidence.timestamp is not None
    relationship = Relationship(
        source_uco="uco-1", target_uco="uco-2", relationship_type="depends_on"
    )
    assert relationship.version == 1
    assert relationship.history == []


def test_episode_extensions() -> None:
    episode = Episode(episode_type="created", description="auth service created")
    assert episode.affected_relationships == []
    assert episode.artifacts == []


def test_memory_expiry_and_edges() -> None:
    working = WorkingMemory(task_id="task-1")
    assert working.expires_at is None
    assert working.token_usage == 0
    knowledge = KnowledgeMemory(organization_id="o")
    assert knowledge.knowledge_edges == []
    assert knowledge.version_history == []


def test_base_event_carries_agent_id() -> None:
    event = BaseEvent(
        event_type="TaskCreated",
        event_category=EventCategory.TASK,
        producer="test",
        agent_id="agent-1",
    )
    assert event.agent_id == "agent-1"
    assert event.event_category is EventCategory.TASK
