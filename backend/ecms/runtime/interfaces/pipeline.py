"""Runtime pipeline collaborator ports (SECTION 92).

The runtime kernel orchestrates the execution pipeline through these ports. Each
is implemented by a later subsystem (planning by the Intelligence Layer, tools by
the Tool Runtime, reflection by the Reflection Engine, promotion by the Knowledge
Promotion Engine). They are optional: the kernel runs the steps it has.
"""

from __future__ import annotations

from typing import Protocol

from ecms.shared.models import (
    ExecutionPlan,
    KnowledgeCandidate,
    Reflection,
    Task,
    ToolExecution,
    UniversalCognitiveObject,
    WorkingMemory,
)

__all__ = ["Planner", "Promoter", "Reflector", "ToolRunner"]


class Planner(Protocol):
    """Converts a prompt and task into an execution plan (SECTION 94)."""

    async def plan(self, task: Task, context: str) -> ExecutionPlan: ...


class ToolRunner(Protocol):
    """Executes the tools required by a task (SECTION 99)."""

    async def run(self, task: Task, working_memory: WorkingMemory) -> list[ToolExecution]: ...


class Reflector(Protocol):
    """Analyzes a completed task and produces a reflection (SECTION 101)."""

    async def reflect(
        self, task: Task, activated: list[UniversalCognitiveObject]
    ) -> Reflection: ...
    async def generate_candidates(
        self,
        task: Task,
        reflection: Reflection,
        activated: list[UniversalCognitiveObject],
    ) -> list[KnowledgeCandidate]: ...


class Promoter(Protocol):
    """Validates and promotes knowledge candidates into knowledge (SECTION 103)."""

    async def promote(
        self, candidates: list[KnowledgeCandidate]
    ) -> list[UniversalCognitiveObject]: ...
