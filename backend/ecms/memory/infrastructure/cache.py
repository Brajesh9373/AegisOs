"""Multi-level memory cache (SECTION 160/161).

The cache stores *references* to knowledge, never the knowledge itself: the
graph remains the single source of truth. It provides a working-memory level
(L1) and a semantic-query level (L4) with hit/miss metrics.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

__all__ = ["MemoryCache"]


class MemoryCache:
    """A reference-only, multi-level cache with hit/miss metrics (SECTION 160)."""

    def __init__(self) -> None:
        """Initialize empty cache levels."""
        self._working: dict[str, list[str]] = {}
        self._semantic: dict[str, list[str]] = {}
        self._hits = 0
        self._misses = 0

    def put_working(self, working_memory_id: str, references: Sequence[str]) -> None:
        """Store the activated references for a working memory (L1)."""
        self._working[working_memory_id] = list(references)

    def get_working(self, working_memory_id: str) -> list[str] | None:
        """Return the cached references for a working memory, if present."""
        return self._working.get(working_memory_id)

    def evict_working(self, working_memory_id: str) -> None:
        """Drop a working memory's cached references (on release)."""
        self._working.pop(working_memory_id, None)

    def cache_query(self, query: str, references: Sequence[str]) -> None:
        """Store the resolved references for a semantic query (L4)."""
        self._semantic[query] = list(references)

    def cached_query(self, query: str) -> list[str] | None:
        """Return cached references for a query, updating hit/miss metrics."""
        cached = self._semantic.get(query)
        if cached is None:
            self._misses += 1
            return None
        self._hits += 1
        return list(cached)

    def statistics(self) -> dict[str, Any]:
        """Return cache occupancy and hit/miss counters."""
        return {
            "working_entries": len(self._working),
            "semantic_entries": len(self._semantic),
            "hits": self._hits,
            "misses": self._misses,
        }
