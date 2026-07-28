"""Memory engine port (SECTION 77).

Memory activates knowledge into a bounded working set; it never owns knowledge.
The engine is a structural port so its implementation remains replaceable.
"""

from __future__ import annotations

from typing import Any, Protocol

from ecms.shared.models import UniversalCognitiveObject, WorkingMemory

__all__ = ["MemoryEngine"]


class MemoryEngine(Protocol):
    """Activates and retrieves knowledge for reasoning (SECTION 77).

    Operations:
        activate: Build a working memory of the most relevant knowledge for a task.
        retrieve: Return ranked cognitive objects for a query.
        release: Release a working memory after task completion.
        statistics: Return activation and cache metrics.
    """

    async def activate(
        self,
        query: str,
        *,
        task_id: str,
        scope: list[str] | None = None,
        activation_limit: int = 10,
    ) -> WorkingMemory: ...
    async def retrieve(self, query: str, *, limit: int = 10) -> list[UniversalCognitiveObject]: ...
    async def release(self, working_memory: WorkingMemory) -> WorkingMemory: ...
    def statistics(self) -> dict[str, Any]: ...
