"""Tests for the intelligence layer (SECTION 283-289)."""

from __future__ import annotations

from pathlib import Path

from ecms.events import InMemoryEventBus
from ecms.intelligence import (
    CapabilityEngine,
    DecisionEngine,
    DefaultPlanner,
    GoalEngine,
    StrategyEngine,
)
from ecms.providers import ConnectorRegistry, FilesystemConnector
from ecms.shared.enums import EventCategory, StrategyType
from ecms.shared.events import BaseEvent
from ecms.shared.models import Task
from ecms.tools import FilesystemTool, ToolRegistry, WorkspaceSandbox


def _task() -> Task:
    return Task(
        session_id="s",
        organization_id="o",
        user_id="u",
        title="feature",
        goal="build it",
    )


def test_goal_engine_decomposes_prompt() -> None:
    goals = GoalEngine().decompose("build auth and add tests")
    assert len(goals) == 2
    assert goals[1].parent_goal == goals[0].goal_id
    assert goals[0].sub_goals == [goals[1].goal_id]


def test_strategy_engine_selects_by_intent() -> None:
    engine = StrategyEngine()
    assert engine.select("write tests", []) is StrategyType.TEST_DRIVEN
    assert engine.select("please review and approve", []) is StrategyType.HUMAN_APPROVAL
    assert engine.select("do it", []) is StrategyType.SEQUENTIAL


def test_decision_engine_records_choice() -> None:
    decision = DecisionEngine().decide(
        question="which db?", chosen="postgres", rationale="acid", confidence=80
    )
    assert decision.chosen == "postgres"
    assert decision.confidence == 80


def test_capability_engine_discovers_registries(tmp_path: Path) -> None:
    tools = ToolRegistry()
    tools.register(FilesystemTool(WorkspaceSandbox(tmp_path)))
    connectors = ConnectorRegistry()
    connectors.register(FilesystemConnector(tmp_path))
    capabilities = CapabilityEngine(tools=tools, connectors=connectors).discover()
    assert "filesystem" in capabilities["tools"]
    assert "filesystem" in capabilities["connectors"]


async def test_planner_produces_plan_and_decision() -> None:
    bus = InMemoryEventBus()
    seen: list[str] = []

    async def handler(event: BaseEvent) -> None:
        seen.append(event.event_type)

    bus.subscribe(handler, category=EventCategory.RUNTIME)
    planner = DefaultPlanner(event_bus=bus)
    plan = await planner.plan(_task(), "build auth and write tests")
    assert plan.strategy is StrategyType.TEST_DRIVEN
    assert len(plan.steps) == 2
    assert plan.plan_id.startswith("plan-")
    assert planner.last_decision is not None
    assert planner.last_decision.chosen == StrategyType.TEST_DRIVEN.value
    assert "PlannerStarted" in seen
    assert "PlannerCompleted" in seen
