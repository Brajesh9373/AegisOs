"""Memory ranking engine (SECTION 159).

Ranks cognitive objects for activation using a configurable weighted blend of
semantic similarity, importance, confidence, business value and recency. Ranking
never mutates knowledge; it only orders references to it.
"""

from __future__ import annotations

from dataclasses import dataclass

from ecms.shared.models import UniversalCognitiveObject
from ecms.shared.time import utcnow

__all__ = ["MemoryRankingEngine", "RankingWeights"]


@dataclass(frozen=True, slots=True)
class RankingWeights:
    """Relative weights for the ranking factors; they need not sum to one."""

    similarity: float = 0.40
    importance: float = 0.25
    confidence: float = 0.20
    business_value: float = 0.10
    recency: float = 0.05


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


class MemoryRankingEngine:
    """Ranks cognitive objects by a configurable weighted score (SECTION 159)."""

    def __init__(self, weights: RankingWeights | None = None) -> None:
        """Initialize with optional custom weights."""
        self._weights = weights or RankingWeights()

    def score(self, uco: UniversalCognitiveObject, *, similarity: float) -> float:
        """Return the ranking score for a cognitive object given a similarity."""
        weights = self._weights
        return (
            weights.similarity * _clamp(similarity)
            + weights.importance * uco.importance / 100.0
            + weights.confidence * uco.confidence / 100.0
            + weights.business_value * uco.business_value / 100.0
            + weights.recency * self._recency(uco)
        )

    @staticmethod
    def _recency(uco: UniversalCognitiveObject) -> float:
        age_days = max((utcnow() - uco.updated_at).days, 0)
        return 1.0 / (1.0 + age_days)
