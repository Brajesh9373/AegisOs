"""Shared keyword matching for the SQL-backed memory layers.

Procedures, preferences-by-keyword, and org patterns are matched with token
overlap rather than embeddings: the sets are small (tens of rows), the
vocabulary is operational ("deploy", "typecheck"), and exact-token matching
is predictable to debug. Episodic/semantic recall keeps using the embedding
index; these helpers cover the layers that have no vector store.
"""

from __future__ import annotations

import re
from typing import Any

__all__ = ["keywords", "rank_by_overlap"]

_TOKEN = re.compile(r"[a-z0-9]+")


def keywords(text: str) -> set[str]:
    """Return significant lowercase tokens (length > 3)."""
    return {t for t in _TOKEN.findall(text.lower()) if len(t) > 3}


def rank_by_overlap(
    query: str, candidates: list[tuple[str, Any]], *, limit: int = 3
) -> list[Any]:
    """Return candidates ordered by shared-token count (best first).

    Args:
        query: The text to match against.
        candidates: (haystack, payload) pairs.
        limit: Max payloads to return.

    Returns:
        Payloads with at least one shared token, best overlap first.
    """
    tokens = keywords(query)
    if not tokens:
        return []
    scored = [
        (sum(1 for t in tokens if t in haystack.lower()), payload)
        for haystack, payload in candidates
    ]
    scored = [(score, payload) for score, payload in scored if score > 0]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [payload for _, payload in scored[:limit]]
