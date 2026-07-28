"""Runtime execution records: runtime context and tool executions (SECTION 46/49).

A :class:`RuntimeContext` is the per-execution context an agent carries so that
subsystems receive scope and budgets explicitly rather than reading global state.
A :class:`ToolExecution` is the permanent record of a single tool invocation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ecms.shared.enums import ToolExecutionStatus
from ecms.shared.ids import new_id
from ecms.shared.models.base import DomainModel
from ecms.shared.value_objects import ExecutionBudget

__all__ = ["RuntimeContext", "ToolExecution"]


def _runtime_context_id() -> str:
    return new_id("rtx")


def _tool_execution_id() -> str:
    return new_id("texec")


class RuntimeContext(DomainModel):
    """The execution context owned by an executing agent (SECTION 49/111).

    Every subsystem receives the runtime context instead of accessing global
    state, keeping executions isolated, explainable and replayable.
    """

    runtime_context_id: str = Field(default_factory=_runtime_context_id)
    agent_id: str
    current_task: str | None = None
    working_memory_id: str | None = None
    knowledge_scope: list[str] = Field(default_factory=list)
    tool_permissions: list[str] = Field(default_factory=list)
    runtime_variables: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, str] = Field(default_factory=dict)
    execution_state: dict[str, Any] = Field(default_factory=dict)
    execution_budget: ExecutionBudget = Field(default_factory=ExecutionBudget)
    timeout_seconds: float | None = Field(default=None, gt=0)
    retry_policy: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    statistics: dict[str, Any] = Field(default_factory=dict)


class ToolExecution(DomainModel):
    """A permanent record of a single tool invocation (SECTION 46).

    Tool executions are auditable: every field required to explain and replay the
    invocation is captured, and the record references the events and artifacts the
    invocation produced.
    """

    execution_id: str = Field(default_factory=_tool_execution_id)
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    caller_agent: str | None = None
    task_id: str | None = None
    session_id: str | None = None
    status: ToolExecutionStatus = ToolExecutionStatus.PENDING
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_ms: float | None = Field(default=None, ge=0)
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    generated_events: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
