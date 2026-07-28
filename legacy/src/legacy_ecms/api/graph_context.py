from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from legacy_ecms.config import get_settings
from legacy_ecms.core.graph import GraphClient
from legacy_ecms.pipeline.orchestrator import PipelineOrchestrator


def create_graph_client() -> GraphClient:
    return GraphClient(get_settings())


@asynccontextmanager
async def orchestrator_context(persist: bool) -> AsyncIterator[PipelineOrchestrator]:
    if not persist:
        yield PipelineOrchestrator()
        return

    graph = create_graph_client()
    await graph.initialize()
    try:
        yield PipelineOrchestrator(graph=graph)
    finally:
        await graph.close()
