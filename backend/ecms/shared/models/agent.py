"""Agent domain model (SECTION 40).

Agents are runtime workers owned by the Runtime, not by the LLM. An agent never
owns knowledge; it is granted a scoped view of knowledge and tools for the
duration of a task, together with explicit execution and token budgets.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ecms.shared.enums import AgentRole, AgentStatus
from ecms.shared.ids import new_id
from ecms.shared.models.base import DomainModel
from ecms.shared.value_objects import ExecutionBudget, TokenBudget

__all__ = ["Agent"]


def _agent_id() -> str:
    return new_id("agent")


class Agent(DomainModel):
    """A runtime worker with a scoped role, permissions, tools and budgets (SECTION 40).

    The Runtime owns the agent and may replace its reasoning model at any time; the
    agent holds only references to knowledge and memory, never the knowledge itself.
    """

    agent_id: str = Field(default_factory=_agent_id)
    role: AgentRole
    status: AgentStatus = AgentStatus.CREATED
    reasoning_model: str = "deterministic"
    permissions: list[str] = Field(default_factory=list)
    tool_access: list[str] = Field(default_factory=list)
    knowledge_scope: list[str] = Field(default_factory=list)
    working_memory_id: str | None = None
    runtime_context_id: str | None = None
    current_task: str | None = None
    execution_budget: ExecutionBudget = Field(default_factory=ExecutionBudget)
    token_budget: TokenBudget = Field(default_factory=TokenBudget)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    policies: list[str] = Field(default_factory=list)
    statistics: dict[str, Any] = Field(default_factory=dict)
