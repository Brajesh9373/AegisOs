"""Strategy engine (SECTION 287).

Chooses how a task should be solved, dynamically, from the prompt and the shape
of the goal decomposition.
"""

from __future__ import annotations

from collections.abc import Sequence

from ecms.shared.enums import StrategyType
from ecms.shared.models import Goal

__all__ = ["StrategyEngine"]


class StrategyEngine:
    """Selects an execution strategy dynamically (SECTION 287)."""

    def select(self, prompt: str, goals: Sequence[Goal]) -> StrategyType:
        """Return the strategy best suited to a prompt and its goals."""
        text = prompt.lower()
        if "test" in text:
            return StrategyType.TEST_DRIVEN
        if "approve" in text or "review" in text:
            return StrategyType.HUMAN_APPROVAL
        if "parallel" in text:
            return StrategyType.PARALLEL
        if len(goals) > 2:
            return StrategyType.HIERARCHICAL
        if "iterate" in text or "refine" in text:
            return StrategyType.ITERATIVE
        return StrategyType.SEQUENTIAL
