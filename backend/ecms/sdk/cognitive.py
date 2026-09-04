"""Cognitive system assembly - the Kernel API (SECTION 90).

Wires the cognition engines (Knowledge, Memory, Graph) and the Runtime Kernel
(with planner, reflection and promotion) into one ready-to-use system that shares
a single knowledge index. This is the preferred entry point for the API, CLI and
SDK.
"""

from __future__ import annotations

from dataclasses import dataclass

from ecms.events import EventBus
from ecms.graph import GraphEngine
from ecms.infrastructure.reasoning import DeterministicEmbeddingProvider
from ecms.intelligence import DefaultPlanner
from ecms.knowledge import DefaultKnowledgeEngine
from ecms.knowledge.infrastructure.repository import InMemoryKnowledgeRepository
from ecms.memory import DefaultMemoryEngine
from ecms.promotion import DefaultPromotionEngine
from ecms.reflection import DefaultReflectionEngine
from ecms.runtime import RuntimeKernel

__all__ = ["CognitiveSystem", "create_cognitive_system"]


@dataclass(frozen=True)
class CognitiveSystem:
    """A fully-wired cognition system exposed through the Kernel API (SECTION 90)."""

    knowledge: DefaultKnowledgeEngine
    memory: DefaultMemoryEngine
    graph: GraphEngine
    kernel: RuntimeKernel
    repository: InMemoryKnowledgeRepository


def create_cognitive_system(
    *,
    event_bus: EventBus | None = None,
    falkordb_url: str | None = None,
    falkordb_graph: str = "ecms",
) -> CognitiveSystem:
    """Assemble the cognition engines and runtime kernel over one knowledge index.

    If falkordb_url is provided, uses the FalkorDB-backed persistent graph store.
    Otherwise defaults to InMemoryGraphStore (for testing/dev).
    """
    embedder = DeterministicEmbeddingProvider()
    repository = InMemoryKnowledgeRepository(embedder)
    knowledge = DefaultKnowledgeEngine(
        embedder=embedder, repository=repository, event_bus=event_bus
    )
    memory = DefaultMemoryEngine(repository, embedder=embedder, event_bus=event_bus)
    if falkordb_url:
        try:
            from ecms.graph.infrastructure.falkordb_store import FalkorDBCypherStore

            store = FalkorDBCypherStore(url=falkordb_url, graph_name=falkordb_graph)
        except Exception:
            from ecms.infrastructure.telemetry import get_logger

            get_logger("ecms.sdk.cognitive").warning(
                "falkordb_unavailable_fallback",
                url=falkordb_url,
            )
            from ecms.graph.infrastructure.memory_store import InMemoryGraphStore

            store = InMemoryGraphStore()
    else:
        from ecms.graph.infrastructure.memory_store import InMemoryGraphStore

        store = InMemoryGraphStore()
    graph = GraphEngine(store=store, event_bus=event_bus)
    kernel = RuntimeKernel(
        knowledge=repository,
        memory=memory,
        graph=graph,
        event_bus=event_bus,
        planner=DefaultPlanner(event_bus=event_bus),
        reflector=DefaultReflectionEngine(event_bus=event_bus),
        promoter=DefaultPromotionEngine(graph=graph, knowledge=repository, event_bus=event_bus),
    )
    return CognitiveSystem(
        knowledge=knowledge,
        memory=memory,
        graph=graph,
        kernel=kernel,
        repository=repository,
    )
