"""Analytics service (SECTION 87/235-241).

Aggregates analytics across cognition domains - graph, memory and promotion - into
a single snapshot for dashboards and Mission Control. It reads statistics from the
engines; it never mutates them.
"""

from __future__ import annotations

from typing import Any

from ecms.graph import GraphEngine
from ecms.memory import DefaultMemoryEngine
from ecms.promotion import DefaultPromotionEngine

__all__ = ["AnalyticsService"]


class AnalyticsService:
    """Aggregates cross-domain analytics (SECTION 87)."""

    def __init__(
        self,
        *,
        graph: GraphEngine | None = None,
        memory: DefaultMemoryEngine | None = None,
        promotion: DefaultPromotionEngine | None = None,
    ) -> None:
        """Initialize with the engines to read analytics from."""
        self._graph = graph
        self._memory = memory
        self._promotion = promotion

    async def graph(self) -> dict[str, Any]:
        """Return graph analytics (SECTION 238)."""
        return await self._graph.statistics() if self._graph is not None else {}

    def memory(self) -> dict[str, Any]:
        """Return memory analytics (SECTION 237)."""
        return self._memory.statistics() if self._memory is not None else {}

    def promotion(self) -> dict[str, int]:
        """Return knowledge-promotion analytics (SECTION 236)."""
        return self._promotion.statistics() if self._promotion is not None else {}

    async def summary(self) -> dict[str, Any]:
        """Return a combined analytics snapshot across domains."""
        return {
            "graph": await self.graph(),
            "memory": self.memory(),
            "promotion": self.promotion(),
        }
