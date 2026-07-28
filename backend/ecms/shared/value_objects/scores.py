"""Bounded score value objects (SECTION 50).

Scores are immutable integers in the inclusive range 0-100 used to quantify
confidence, importance, business value, stability and reusability across the
platform. They compare by value and type, and expose a normalized fraction so
ranking and threshold logic can operate on a 0.0-1.0 scale.
"""

from __future__ import annotations

from typing import Self

from pydantic import Field

from ecms.shared.value_objects.base import ValueObject

__all__ = [
    "BusinessValueScore",
    "ConfidenceScore",
    "ImportanceScore",
    "ReusabilityScore",
    "Score",
    "StabilityScore",
]


class Score(ValueObject):
    """Immutable score in the inclusive range 0-100 (SECTION 50)."""

    value: int = Field(ge=0, le=100)

    @property
    def fraction(self) -> float:
        """Return the score normalized to the inclusive range 0.0-1.0."""
        return self.value / 100.0

    @classmethod
    def from_fraction(cls, fraction: float) -> Self:
        """Build a score from a 0.0-1.0 fraction, clamping out-of-range input.

        Args:
            fraction: A value that is clamped to the inclusive range 0.0-1.0
                before being scaled to the 0-100 score range.

        Returns:
            A new score of the concrete subclass on which this is called.
        """
        clamped = min(1.0, max(0.0, fraction))
        return cls(value=round(clamped * 100))


class ConfidenceScore(Score):
    """Confidence that a piece of understanding is correct (SECTION 37)."""


class ImportanceScore(Score):
    """Importance of a cognitive object to the organization (SECTION 37)."""


class BusinessValueScore(Score):
    """Business value attributed to a cognitive object (SECTION 37)."""


class StabilityScore(Score):
    """Stability of a cognitive object over time; higher is more stable (SECTION 37)."""


class ReusabilityScore(Score):
    """Reusability of a cognitive object across contexts (SECTION 37)."""
