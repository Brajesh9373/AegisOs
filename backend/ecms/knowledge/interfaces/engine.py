"""Knowledge engine and repository ports (SECTION 75).

The Knowledge Engine transforms information (UKOs) into understanding (UCOs). The
:class:`KnowledgeRepository` persists and searches the cognitive objects it
produces. Both are structural ports so implementations remain replaceable.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ecms.shared.models import UniversalCognitiveObject, UniversalKnowledgeObject

__all__ = ["KnowledgeEngine", "KnowledgeRepository"]


@runtime_checkable
class KnowledgeRepository(Protocol):
    """Persistence and retrieval port for cognitive objects (SECTION 75).

    Operations:
        add: Persist a cognitive object and index it for search.
        get: Return a cognitive object by id, or ``None``.
        all: Return every stored cognitive object.
        search: Return the objects most semantically similar to a query.
    """

    async def add(self, uco: UniversalCognitiveObject) -> None: ...
    async def get(self, uco_id: str) -> UniversalCognitiveObject | None: ...
    async def all(self) -> list[UniversalCognitiveObject]: ...
    async def search(self, query: str, *, limit: int = 10) -> list[UniversalCognitiveObject]: ...
    async def reindex(self) -> int: ...


class KnowledgeEngine(Protocol):
    """Transforms information into organizational understanding (SECTION 29/75).

    Operations:
        ingest: Run the full pipeline for a UKO and return generated UCOs.
        generate_uco: Build a single cognitive object from a UKO and an entity.
        validate: Return the validation status of a cognitive object.
        publish: Persist cognitive objects and emit knowledge events.
        search: Return cognitive objects matching a query.
        merge: Merge duplicate cognitive objects into one.
        reindex: Rebuild the search index; return the number of objects indexed.
    """

    async def ingest(self, uko: UniversalKnowledgeObject) -> list[UniversalCognitiveObject]: ...
    async def search(self, query: str, *, limit: int = 10) -> list[UniversalCognitiveObject]: ...
    async def reindex(self) -> int: ...
