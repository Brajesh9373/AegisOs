"""Graph engine over the single enterprise cognitive graph (SECTION 76/143-146).

The engine owns node and relationship lifecycle, traversal (neighbors, shortest
path, multi-hop expansion), graph views (projections of the one graph) and
statistics. It performs no reasoning; it operates through a replaceable store.
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Any

from ecms.events import EventBus
from ecms.graph.domain.graph import GraphEdge, GraphNode, Subgraph, deterministic_edge_id
from ecms.graph.events.graph_events import (
    node_created,
    node_deleted,
    node_updated,
    relationship_created,
    relationship_deleted,
)
from ecms.graph.infrastructure.memory_store import InMemoryGraphStore
from ecms.graph.interfaces.graph import GraphStore
from ecms.shared.events import BaseEvent
from ecms.shared.models import UniversalCognitiveObject

__all__ = ["GraphEngine"]


class GraphEngine:
    """Owns the enterprise cognitive graph through a replaceable store (SECTION 76)."""

    def __init__(
        self, store: GraphStore | None = None, *, event_bus: EventBus | None = None
    ) -> None:
        """Initialize the engine with a graph store and optional event bus."""
        self._store = store or InMemoryGraphStore()
        self._event_bus = event_bus

    async def upsert_uco(self, uco: UniversalCognitiveObject) -> GraphNode:
        """Project a cognitive object into a node, versioning on update (SECTION 137)."""
        existing = await self._store.get_node(uco.uco_id)
        version = existing.version + 1 if existing is not None else 1
        node = GraphNode(
            node_id=uco.uco_id,
            ontology_type=uco.ontology_type,
            display_name=uco.display_name,
            canonical_name=uco.canonical_name,
            confidence=uco.confidence,
            importance=uco.importance,
            version=version,
            properties={"summary": uco.summary or ""},
        )
        await self._store.upsert_node(node)
        event_payload = {
            "node_id": node.node_id,
            "display_name": node.display_name,
            "ontology_type": node.ontology_type,
            "confidence": node.confidence,
            "importance": node.importance,
        }
        if existing is not None:
            await self._emit(node_updated(**event_payload))
        else:
            await self._emit(node_created(**event_payload))
        return node

    async def create_relationship(
        self,
        source: str,
        target: str,
        relationship_type: str,
        *,
        weight: float = 1.0,
        confidence: int = 0,
    ) -> GraphEdge:
        """Create a relationship edge between two nodes (SECTION 138).

        Edge IDs are deterministic (sha256(source|target|type)) so repeated
        calls with the same arguments are idempotent — no duplicate edges.
        """
        edge_id = deterministic_edge_id(source, target, relationship_type)
        edge = GraphEdge(
            edge_id=edge_id,
            source=source,
            target=target,
            relationship_type=relationship_type,
            weight=weight,
            confidence=confidence,
        )
        await self._store.upsert_edge(edge)
        await self._emit(
            relationship_created(
                edge.edge_id,
                source=edge.source,
                target=edge.target,
                relationship_type=edge.relationship_type,
                weight=edge.weight,
                confidence=edge.confidence,
            )
        )
        return edge

    async def find_node(self, node_id: str) -> GraphNode | None:
        """Return a node by id, or ``None``."""
        return await self._store.get_node(node_id)

    async def neighbors(self, node_id: str) -> list[GraphNode]:
        """Return the nodes adjacent to a node."""
        return await self._store.neighbors(node_id)

    async def delete_node(self, node_id: str) -> None:
        """Delete a node and its incident edges."""
        await self._store.delete_node(node_id)
        await self._emit(node_deleted(node_id))

    async def delete_relationship(self, edge_id: str) -> None:
        """Delete a relationship edge."""
        await self._store.delete_edge(edge_id)
        await self._emit(relationship_deleted(edge_id))

    async def shortest_path(self, source: str, target: str) -> list[str]:
        """Return a shortest path of node ids from source to target (SECTION 144).

        Returns an empty list when no path exists.
        """
        if source == target:
            return [source] if await self._store.get_node(source) is not None else []
        visited = {source}
        queue: deque[list[str]] = deque([[source]])
        while queue:
            path = queue.popleft()
            for neighbor in await self._store.neighbors(path[-1]):
                if neighbor.node_id == target:
                    return [*path, target]
                if neighbor.node_id not in visited:
                    visited.add(neighbor.node_id)
                    queue.append([*path, neighbor.node_id])
        return []

    async def expand(self, node_id: str, *, hops: int = 1) -> Subgraph:
        """Return the neighborhood subgraph within ``hops`` of a node (SECTION 145)."""
        start = await self._store.get_node(node_id)
        if start is None:
            return Subgraph()
        collected: dict[str, GraphNode] = {node_id: start}
        edges: dict[str, GraphEdge] = {}
        frontier = [node_id]
        for _ in range(max(hops, 0)):
            next_frontier: list[str] = []
            for current in frontier:
                for edge in await self._store.edges_of(current):
                    edges[edge.edge_id] = edge
                    for other in (edge.source, edge.target):
                        if other not in collected:
                            node = await self._store.get_node(other)
                            if node is not None:
                                collected[other] = node
                                next_frontier.append(other)
            frontier = next_frontier
        return Subgraph(nodes=list(collected.values()), edges=list(edges.values()))

    async def view(
        self, *, ontology_type: str | None = None, node_ids: list[str] | None = None
    ) -> Subgraph:
        """Return a projection (view) of the one graph; never a copy (SECTION 143)."""
        nodes = await self._store.all_nodes()
        if ontology_type is not None:
            nodes = [node for node in nodes if node.ontology_type == ontology_type]
        if node_ids is not None:
            allowed = set(node_ids)
            nodes = [node for node in nodes if node.node_id in allowed]
        selected = {node.node_id for node in nodes}
        edges = [
            edge
            for edge in await self._store.all_edges()
            if edge.source in selected and edge.target in selected
        ]
        return Subgraph(nodes=nodes, edges=edges)

    async def statistics(self) -> dict[str, Any]:
        """Return graph analytics: counts, density and ontology distribution (SECTION 146)."""
        nodes = await self._store.all_nodes()
        edges = await self._store.all_edges()
        node_count = len(nodes)
        edge_count = len(edges)
        possible = node_count * (node_count - 1)
        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "density": edge_count / possible if possible else 0.0,
            "ontology_distribution": dict(Counter(node.ontology_type for node in nodes)),
        }

    async def _emit(self, event: BaseEvent) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)
