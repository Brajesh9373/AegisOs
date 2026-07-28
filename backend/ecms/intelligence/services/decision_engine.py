"""Decision engine (SECTION 288/297).

Produces explainable, traceable decision records. Every decision answers why it
was made and which alternatives were rejected.
"""

from __future__ import annotations

from typing import Any

from ecms.shared.enums import StrategyType
from ecms.shared.models import Decision

__all__ = ["DecisionEngine"]


class DecisionEngine:
    """Records explainable decisions made during reasoning (SECTION 288)."""

    def decide(
        self,
        *,
        question: str,
        chosen: str,
        rationale: str,
        task_id: str | None = None,
        considered: list[str] | None = None,
        rejected: list[dict[str, Any]] | None = None,
        strategy: StrategyType | None = None,
        confidence: int = 70,
    ) -> Decision:
        """Create and return a traceable decision record."""
        return Decision(
            task_id=task_id,
            question=question,
            chosen=chosen,
            rationale=rationale,
            considered_options=considered or [],
            rejected_options=rejected or [],
            strategy=strategy,
            confidence=confidence,
        )
