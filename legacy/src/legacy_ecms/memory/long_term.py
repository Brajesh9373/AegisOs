from typing import Any

from legacy_ecms.core.episode import EpisodePayload
from legacy_ecms.core.graph import BatchWriteResult, GraphClient
from legacy_ecms.core.uko import UniversalKnowledgeObject
from legacy_ecms.pipeline.orchestrator import PipelineOrchestrator


class LongTermMemory:
    """Long-term memory facade over Graphiti/FalkorDB."""

    def __init__(self, graph: GraphClient | None = None) -> None:
        self.graph = graph

    async def remember(self, uko: UniversalKnowledgeObject) -> tuple[list[EpisodePayload], BatchWriteResult]:
        return await PipelineOrchestrator(graph=self.graph).process_uko(uko)

    async def search(self, query: str, num_results: int = 10) -> Any:
        if self.graph is None:
            return []
        return await self.graph.search(query=query, num_results=num_results)
