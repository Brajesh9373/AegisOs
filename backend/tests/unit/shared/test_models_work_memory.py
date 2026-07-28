"""Tests for the task, session and memory domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ecms.shared.enums import MemoryStatus, SessionStatus, TaskPriority, TaskStatus
from ecms.shared.models import (
    KnowledgeMemory,
    Session,
    SessionMemory,
    Task,
    WorkingMemory,
)


def test_task_defaults() -> None:
    task = Task(
        session_id="session-1",
        organization_id="org-1",
        user_id="user-1",
        title="Add auth",
        goal="Implement authentication",
    )
    assert task.task_id.startswith("task-")
    assert task.status is TaskStatus.CREATED
    assert task.priority is TaskPriority.MEDIUM


def test_session_defaults() -> None:
    session = Session(organization_id="org-1", user_id="user-1")
    assert session.session_id.startswith("session-")
    assert session.status is SessionStatus.ACTIVE


def test_working_memory_defaults_and_budget_validation() -> None:
    memory = WorkingMemory(task_id="task-1")
    assert memory.working_memory_id.startswith("wm-")
    assert memory.status is MemoryStatus.ACTIVE
    with pytest.raises(ValidationError):
        WorkingMemory(task_id="task-1", token_budget=-1)


def test_session_memory_id_prefix() -> None:
    memory = SessionMemory(session_id="session-1")
    assert memory.session_memory_id.startswith("sm-")


def test_knowledge_memory_id_prefix() -> None:
    memory = KnowledgeMemory(organization_id="org-1")
    assert memory.knowledge_memory_id.startswith("km-")
