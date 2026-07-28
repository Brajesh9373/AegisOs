"""Task and session domain models (SECTION 24/25).

A task is the smallest executable unit created by a user request. A session is a
collaborative workspace that contains multiple tasks.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ecms.shared.enums import SessionStatus, TaskPriority, TaskStatus
from ecms.shared.ids import new_id
from ecms.shared.models.base import AggregateRoot, Attachment
from ecms.shared.time import utcnow

__all__ = ["Session", "Task"]


def _task_id() -> str:
    return new_id("task")


def _session_id() -> str:
    return new_id("session")


class Task(AggregateRoot):
    """The smallest executable unit created by a user request (SECTION 24)."""

    task_id: str = Field(default_factory=_task_id)
    session_id: str
    organization_id: str
    user_id: str
    title: str
    goal: str
    description: str | None = None
    parent_task: str | None = None
    child_tasks: list[str] = Field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.CREATED
    started_at: datetime | None = None
    completed_at: datetime | None = None
    assigned_agents: list[str] = Field(default_factory=list)
    working_memory_id: str | None = None
    planner_output: dict[str, Any] | None = None
    execution_plan: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    generated_artifacts: list[dict[str, Any]] = Field(default_factory=list)
    knowledge_candidates: list[str] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    summary: str | None = None
    reflection_id: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class Session(AggregateRoot):
    """A collaborative workspace containing multiple tasks (SECTION 25)."""

    session_id: str = Field(default_factory=_session_id)
    organization_id: str
    workspace_id: str | None = None
    project_id: str | None = None
    user_id: str
    participants: list[str] = Field(default_factory=list)
    status: SessionStatus = SessionStatus.ACTIVE
    started_at: datetime = Field(default_factory=utcnow)
    ended_at: datetime | None = None
    active_tasks: list[str] = Field(default_factory=list)
    completed_tasks: list[str] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    session_summary: str | None = None
    architectural_decisions: list[dict[str, Any]] = Field(default_factory=list)
    active_knowledge: list[str] = Field(default_factory=list)
    knowledge_statistics: dict[str, Any] = Field(default_factory=dict)
    memory_statistics: dict[str, Any] = Field(default_factory=dict)
    events: list[str] = Field(default_factory=list)
    graph_view: dict[str, Any] | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
