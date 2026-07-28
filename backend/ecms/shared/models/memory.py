"""Working, session and knowledge memory models (SECTION 26/27/28).

Memory activates knowledge; it never owns it. Working memory is a short-lived execution
workspace, session memory accumulates understanding across tasks, and knowledge memory
indexes permanent organizational understanding.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ecms.shared.enums import MemoryStatus
from ecms.shared.ids import new_id
from ecms.shared.models.base import DomainModel

__all__ = ["KnowledgeMemory", "SessionMemory", "WorkingMemory"]


def _working_memory_id() -> str:
    return new_id("wm")


def _session_memory_id() -> str:
    return new_id("sm")


def _knowledge_memory_id() -> str:
    return new_id("km")


class WorkingMemory(DomainModel):
    """Short-lived execution workspace for a task; never owns knowledge (SECTION 26)."""

    working_memory_id: str = Field(default_factory=_working_memory_id)
    task_id: str
    active_uco_references: list[str] = Field(default_factory=list)
    execution_plan: list[dict[str, Any]] = Field(default_factory=list)
    planner_state: dict[str, Any] = Field(default_factory=dict)
    reasoning_state: dict[str, Any] = Field(default_factory=dict)
    tool_state: dict[str, Any] = Field(default_factory=dict)
    scratchpad: str = ""
    temporary_variables: dict[str, Any] = Field(default_factory=dict)
    intermediate_results: list[dict[str, Any]] = Field(default_factory=list)
    execution_timeline: list[dict[str, Any]] = Field(default_factory=list)
    token_budget: int | None = Field(default=None, ge=0)
    memory_budget: int | None = Field(default=None, ge=0)
    activation_budget: int | None = Field(default=None, ge=0)
    token_usage: int = Field(default=0, ge=0)
    status: MemoryStatus = MemoryStatus.ACTIVE
    expires_at: datetime | None = None


class SessionMemory(DomainModel):
    """Accumulates organizational understanding across tasks in a session (SECTION 27)."""

    session_memory_id: str = Field(default_factory=_session_memory_id)
    session_id: str
    activated_uco_references: list[str] = Field(default_factory=list)
    completed_task_summaries: list[dict[str, Any]] = Field(default_factory=list)
    architectural_decisions: list[dict[str, Any]] = Field(default_factory=list)
    conversation_summary: str | None = None
    session_statistics: dict[str, Any] = Field(default_factory=dict)
    activation_history: list[dict[str, Any]] = Field(default_factory=list)
    memory_events: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None


class KnowledgeMemory(DomainModel):
    """Index of permanent organizational understanding (SECTION 28)."""

    knowledge_memory_id: str = Field(default_factory=_knowledge_memory_id)
    organization_id: str
    uco_references: list[str] = Field(default_factory=list)
    knowledge_statistics: dict[str, Any] = Field(default_factory=dict)
    ontology_statistics: dict[str, Any] = Field(default_factory=dict)
    activation_statistics: dict[str, Any] = Field(default_factory=dict)
    promotion_statistics: dict[str, Any] = Field(default_factory=dict)
    retention_policies: list[dict[str, Any]] = Field(default_factory=list)
    security_statistics: dict[str, Any] = Field(default_factory=dict)
    knowledge_edges: list[str] = Field(default_factory=list)
    archive_policy: dict[str, Any] = Field(default_factory=dict)
    governance_policy: dict[str, Any] = Field(default_factory=dict)
    version_history: list[dict[str, Any]] = Field(default_factory=list)
