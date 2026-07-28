"""Default memory engine (SECTION 77/157/158).

Implements the memory activation pipeline: retrieve candidate knowledge from the
Knowledge index, score it by similarity and cognitive attributes, and activate a
bounded working set. Memory holds only references to knowledge; the graph remains
the source of truth. Reasoning and embedding are supplied by replaceable
providers.
"""

from __future__ import annotations

from typing import Any

from ecms.events import EventBus
from ecms.infrastructure.reasoning import (
    DeterministicEmbeddingProvider,
    DeterministicReasoningProvider,
)
from ecms.knowledge.infrastructure.repository import cosine_similarity
from ecms.knowledge.interfaces.engine import KnowledgeRepository
from ecms.memory.events.memory_events import (
    working_memory_activated,
    working_memory_created,
    working_memory_released,
)
from ecms.memory.infrastructure.cache import MemoryCache
from ecms.memory.infrastructure.ranking import MemoryRankingEngine
from ecms.shared.enums import MemoryStatus
from ecms.shared.events import BaseEvent
from ecms.shared.interfaces import EmbeddingProvider, ReasoningProvider, ReasoningRequest
from ecms.shared.models import UniversalCognitiveObject, WorkingMemory
from ecms.shared.time import utcnow

__all__ = ["DefaultMemoryEngine"]

_Scored = tuple[UniversalCognitiveObject, float]


class DefaultMemoryEngine:
    """Activates and retrieves knowledge without ever owning it (SECTION 77)."""

    def __init__(
        self,
        knowledge: KnowledgeRepository,
        *,
        embedder: EmbeddingProvider | None = None,
        reasoner: ReasoningProvider | None = None,
        ranker: MemoryRankingEngine | None = None,
        cache: MemoryCache | None = None,
        event_bus: EventBus | None = None,
        candidate_pool: int = 25,
    ) -> None:
        """Initialize the engine with a knowledge index and replaceable providers."""
        self._knowledge = knowledge
        self._embedder = embedder or DeterministicEmbeddingProvider()
        self._reasoner = reasoner or DeterministicReasoningProvider()
        self._ranker = ranker or MemoryRankingEngine()
        self._cache = cache or MemoryCache()
        self._event_bus = event_bus
        self._pool = candidate_pool
        self._activations = 0

    async def activate(
        self,
        query: str,
        *,
        task_id: str,
        scope: list[str] | None = None,
        activation_limit: int = 10,
    ) -> WorkingMemory:
        """Activate the most relevant knowledge into a bounded working memory (SECTION 157)."""
        ranked = await self._rank_candidates(query, scope=scope)
        references = [uco.uco_id for uco, _ in ranked[:activation_limit]]
        working = WorkingMemory(
            task_id=task_id,
            active_uco_references=references,
            activation_budget=activation_limit,
        )
        self._cache.put_working(working.working_memory_id, references)
        self._activations += 1
        await self._emit(working_memory_created(working.working_memory_id))
        await self._emit(working_memory_activated(working.working_memory_id, len(references)))
        return working

    async def retrieve(self, query: str, *, limit: int = 10) -> list[UniversalCognitiveObject]:
        """Return ranked cognitive objects for a query, using the semantic cache (SECTION 158)."""
        cached = self._cache.cached_query(query)
        if cached is not None:
            resolved = [await self._knowledge.get(reference) for reference in cached]
            return [uco for uco in resolved if uco is not None][:limit]
        ranked = await self._rank_candidates(query, scope=None)
        results = [uco for uco, _ in ranked[:limit]]
        self._cache.cache_query(query, [uco.uco_id for uco in results])
        return results

    async def release(self, working_memory: WorkingMemory) -> WorkingMemory:
        """Release a working memory after task completion (SECTION 105)."""
        self._cache.evict_working(working_memory.working_memory_id)
        released = working_memory.model_copy(
            update={"status": MemoryStatus.RELEASED, "expires_at": utcnow()}
        )
        await self._emit(working_memory_released(working_memory.working_memory_id))
        return released

    async def compress(self, text: str) -> str:
        """Compress context into a concise summary, preserving meaning (SECTION 163)."""
        response = await self._reasoner.reason(
            ReasoningRequest(
                instruction="compress the following into a concise summary",
                context=text,
            )
        )
        return response.content

    def statistics(self) -> dict[str, Any]:
        """Return activation and cache metrics (SECTION 166)."""
        return {"activations": self._activations, "cache": self._cache.statistics()}

    async def _rank_candidates(self, query: str, *, scope: list[str] | None) -> list[_Scored]:
        candidates = await self._knowledge.search(query, limit=self._pool)
        if scope is not None:
            allowed = set(scope)
            candidates = [uco for uco in candidates if uco.uco_id in allowed]
        query_vector = await self._embedder.embed(query)
        scored: list[_Scored] = []
        for uco in candidates:
            vector = await self._embedder.embed(
                f"{uco.display_name} {uco.ontology_type} {uco.description}"
            )
            similarity = cosine_similarity(query_vector, vector)
            scored.append((uco, self._ranker.score(uco, similarity=similarity)))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    async def _emit(self, event: BaseEvent) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)
