"""Reflection engine port (SECTION 78).

Reflection learns from execution and proposes knowledge candidates; it never
modifies enterprise knowledge.
"""

from __future__ import annotations

from typing import Protocol

from ecms.shared.models import (
    KnowledgeCandidate,
    Reflection,
    Task,
    UniversalCognitiveObject,
)

__all__ = ["ReflectionEngine"]


class ReflectionEngine(Protocol):
    """Analyzes tasks and proposes learning (SECTION 78).

    Operations:
        reflect: Analyze a completed task and return a reflection.
        generate_candidates: Turn a reflection into isolated knowledge candidates.
    """

    async def reflect(
        self, task: Task, activated: list[UniversalCognitiveObject]
    ) -> Reflection: ...
    async def generate_candidates(
        self,
        task: Task,
        reflection: Reflection,
        activated: list[UniversalCognitiveObject],
    ) -> list[KnowledgeCandidate]: ...
