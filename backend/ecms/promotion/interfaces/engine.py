"""Knowledge promotion engine port (SECTION 79).

Promotion is the only path that may modify enterprise knowledge. No agent writes
knowledge directly.
"""

from __future__ import annotations

from typing import Protocol

from ecms.shared.models import KnowledgeCandidate, UniversalCognitiveObject

__all__ = ["PromotionEngine"]


class PromotionEngine(Protocol):
    """Validates and promotes knowledge candidates (SECTION 79).

    Operations:
        promote: Validate, de-duplicate and promote candidates into knowledge.
        statistics: Return promotion counters.
    """

    async def promote(
        self, candidates: list[KnowledgeCandidate]
    ) -> list[UniversalCognitiveObject]: ...
    def statistics(self) -> dict[str, int]: ...
