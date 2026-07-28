"""Workflow engine (SECTION 271).

Plugins register workflows - ordered steps, each an async action optionally gated
by a condition. The Runtime executes a workflow by threading a shared context
through its steps, skipping steps whose condition is not met.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from ecms.shared.exceptions import NotFoundError

__all__ = ["Workflow", "WorkflowEngine", "WorkflowStep"]

WorkflowAction = Callable[[dict[str, Any]], Awaitable[Any]]
WorkflowCondition = Callable[[dict[str, Any]], bool]


@dataclass(slots=True)
class WorkflowStep:
    """A single workflow step: an action, optionally gated by a condition."""

    name: str
    action: WorkflowAction
    condition: WorkflowCondition | None = None


@dataclass(slots=True)
class Workflow:
    """An ordered, named sequence of workflow steps (SECTION 271)."""

    name: str
    steps: list[WorkflowStep] = field(default_factory=list)

    def step(
        self,
        name: str,
        action: WorkflowAction,
        *,
        condition: WorkflowCondition | None = None,
    ) -> Workflow:
        """Append a step and return the workflow for fluent chaining."""
        self.steps.append(WorkflowStep(name=name, action=action, condition=condition))
        return self


class WorkflowEngine:
    """Registers and executes plugin workflows (SECTION 271)."""

    def __init__(self) -> None:
        """Initialize an empty workflow registry."""
        self._workflows: dict[str, Workflow] = {}

    def register(self, workflow: Workflow) -> None:
        """Register a workflow by name."""
        self._workflows[workflow.name] = workflow

    async def execute(self, name: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a workflow, threading a shared context through its steps.

        Raises:
            NotFoundError: If no workflow is registered under ``name``.
        """
        workflow = self._workflows.get(name)
        if workflow is None:
            raise NotFoundError(f"workflow {name!r} is not registered")
        state: dict[str, Any] = dict(context or {})
        executed: list[str] = []
        for step in workflow.steps:
            if step.condition is not None and not step.condition(state):
                continue
            result = await step.action(state)
            if isinstance(result, dict):
                state.update(result)
            state[f"{step.name}_result"] = result
            executed.append(step.name)
        state["_executed"] = executed
        return state
