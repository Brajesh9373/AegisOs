"""In-memory knowledge repository with semantic search (SECTION 75/95).

Cognitive objects are indexed with an embedding provider so retrieval is by
meaning, not keywords. The graph remains the source of truth in production; this
repository is the default index used offline and in tests.
"""

from __future__ import annotations

from ecms.shared.interfaces import EmbeddingProvider, EmbeddingVector
from ecms.shared.models import UniversalCognitiveObject

__all__ = ["InMemoryKnowledgeRepository", "cosine_similarity"]


def cosine_similarity(left: EmbeddingVector, right: EmbeddingVector) -> float:
    """Return the cosine similarity of two equal-length embedding vectors."""
    return sum(a * b for a, b in zip(left.values, right.values, strict=True))


class InMemoryKnowledgeRepository:
    """An in-memory, embedding-indexed store of cognitive objects (SECTION 75)."""

    def __init__(self, embedder: EmbeddingProvider) -> None:
        """Initialize the repository with an embedding provider for indexing."""
        self._embedder = embedder
        self._objects: dict[str, UniversalCognitiveObject] = {}
        self._vectors: dict[str, EmbeddingVector] = {}

    def _text(self, uco: UniversalCognitiveObject) -> str:
        return f"{uco.display_name} {uco.canonical_name} {uco.ontology_type} {uco.description}"

    async def add(self, uco: UniversalCognitiveObject) -> None:
        """Persist a cognitive object and index its embedding for search."""
        self._objects[uco.uco_id] = uco
        self._vectors[uco.uco_id] = await self._embedder.embed(self._text(uco))

    async def get(self, uco_id: str) -> UniversalCognitiveObject | None:
        """Return a cognitive object by id, or ``None`` if absent."""
        return self._objects.get(uco_id)

    async def all(self) -> list[UniversalCognitiveObject]:
        """Return every stored cognitive object."""
        return list(self._objects.values())

    async def search(self, query: str, *, limit: int = 10) -> list[UniversalCognitiveObject]:
        """Return the cognitive objects most similar to ``query``, best first."""
        if not self._vectors:
            return []
        query_vector = await self._embedder.embed(query)
        ranked = sorted(
            self._vectors.items(),
            key=lambda item: cosine_similarity(query_vector, item[1]),
            reverse=True,
        )
        return [self._objects[uco_id] for uco_id, _ in ranked[:limit]]

    async def reindex(self) -> int:
        """Recompute every embedding; return the number of objects indexed."""
        for uco in list(self._objects.values()):
            self._vectors[uco.uco_id] = await self._embedder.embed(self._text(uco))
        return len(self._objects)
