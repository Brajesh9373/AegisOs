"""Tests for the workflow and automation engines (SECTION 271/272)."""

from __future__ import annotations

from typing import Any

import pytest

from ecms.events import InMemoryEventBus
from ecms.plugins import AutomationEngine, Workflow, WorkflowEngine
from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent, make_event


async def test_workflow_threads_context_through_steps() -> None:
    async def step_one(state: dict[str, Any]) -> dict[str, Any]:
        return {"count": state.get("count", 0) + 1}

    async def step_two(state: dict[str, Any]) -> dict[str, Any]:
        return {"count": state["count"] + 1}

    workflow = Workflow("demo").step("one", step_one).step("two", step_two)
    engine = WorkflowEngine()
    engine.register(workflow)
    result = await engine.execute("demo", {"count": 0})
    assert result["count"] == 2
    assert result["_executed"] == ["one", "two"]


async def test_workflow_skips_steps_when_condition_false() -> None:
    async def guarded(state: dict[str, Any]) -> dict[str, Any]:
        return {"ran": True}

    workflow = Workflow("demo").step(
        "guarded", guarded, condition=lambda state: state.get("enabled", False)
    )
    engine = WorkflowEngine()
    engine.register(workflow)
    result = await engine.execute("demo", {"enabled": False})
    assert result["_executed"] == []


async def test_workflow_missing_raises() -> None:
    from ecms.shared.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        await WorkflowEngine().execute("nope")


async def test_automation_triggers_on_matching_event() -> None:
    engine = AutomationEngine()
    handled: list[str] = []

    async def handler(event: BaseEvent) -> None:
        handled.append(event.event_type)

    engine.on("TaskCompleted", handler)
    await engine.trigger(make_event("TaskCompleted", EventCategory.TASK, "test"))
    await engine.trigger(make_event("TaskFailed", EventCategory.TASK, "test"))
    assert handled == ["TaskCompleted"]
    assert engine.fired == 1


async def test_automation_subscribes_to_event_bus() -> None:
    bus = InMemoryEventBus()
    engine = AutomationEngine(event_bus=bus)
    handled: list[str] = []

    async def handler(event: BaseEvent) -> None:
        handled.append(event.event_type)

    engine.on("KnowledgePromoted", handler)
    await bus.publish(make_event("KnowledgePromoted", EventCategory.KNOWLEDGE, "test"))
    assert handled == ["KnowledgePromoted"]
