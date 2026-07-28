"""Tests for the runtime managers (SECTION 72/73/74)."""

from __future__ import annotations

import pytest

from ecms.runtime import AgentOrchestrator, SessionManager, TaskManager
from ecms.shared.enums import AgentRole, AgentStatus, SessionStatus, TaskStatus
from ecms.shared.exceptions import NotFoundError


async def test_task_lifecycle_and_hierarchy() -> None:
    manager = TaskManager()
    root = await manager.create(
        session_id="s", organization_id="o", user_id="u", goal="build feature"
    )
    child = await manager.create(
        session_id="s",
        organization_id="o",
        user_id="u",
        goal="subtask",
        parent_task=root.task_id,
    )
    assert child.parent_task == root.task_id
    assert [task.task_id for task in manager.children(root.task_id)] == [child.task_id]

    started = await manager.start(root.task_id)
    assert started.status is TaskStatus.RUNNING
    assert started.started_at is not None
    completed = await manager.complete(root.task_id, summary="done")
    assert completed.status is TaskStatus.COMPLETED
    assert completed.summary == "done"


async def test_task_failure_and_retry() -> None:
    manager = TaskManager()
    task = await manager.create(session_id="s", organization_id="o", user_id="u", goal="x")
    failed = await manager.fail(task.task_id, "boom")
    assert failed.status is TaskStatus.FAILED
    assert "boom" in failed.errors
    retried = await manager.retry(task.task_id)
    assert retried.status is TaskStatus.QUEUED


async def test_task_manager_requires_existing_task() -> None:
    manager = TaskManager()
    with pytest.raises(NotFoundError):
        await manager.start("missing")


async def test_session_lifecycle() -> None:
    manager = SessionManager()
    session = await manager.create(organization_id="o", user_id="u")
    await manager.add_task(session.session_id, "task-1")
    assert session.active_tasks == ["task-1"]
    await manager.complete_task(session.session_id, "task-1")
    assert session.completed_tasks == ["task-1"]
    closed = await manager.close(session.session_id, summary="wrap up")
    assert closed.status is SessionStatus.COMPLETED
    assert closed.ended_at is not None


async def test_agent_orchestrator() -> None:
    orchestrator = AgentOrchestrator()
    agent = await orchestrator.create(AgentRole.BACKEND_ENGINEER)
    assigned = await orchestrator.assign(agent.agent_id, "task-1")
    assert assigned.status is AgentStatus.EXECUTING
    assert assigned.current_task == "task-1"
    stopped = await orchestrator.stop(agent.agent_id)
    assert stopped.status is AgentStatus.STOPPED
