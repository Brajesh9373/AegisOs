"""Runtime execution result (SECTION 92/112).

A structured, reproducible record of one pipeline execution: the session and task
it ran under, the knowledge it activated, and the artifacts, reflection and
candidates it produced.
"""

from __future__ import annotations

from pydantic import Field

from ecms.shared.models.base import DomainModel

__all__ = ["ExecutionResult"]


class ExecutionResult(DomainModel):
    """The outcome of a single runtime execution (SECTION 92)."""

    session_id: str
    task_id: str
    status: str = "completed"
    activated_uco_ids: list[str] = Field(default_factory=list)
    plan_id: str | None = None
    agent_id: str | None = None
    tool_executions: list[str] = Field(default_factory=list)
    reflection_id: str | None = None
    knowledge_candidates: list[str] = Field(default_factory=list)
    graph_nodes: list[str] = Field(default_factory=list)
    summary: str | None = None
