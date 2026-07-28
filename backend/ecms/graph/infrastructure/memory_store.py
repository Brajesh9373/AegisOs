"""In-memory graph store with adjacency indexes (SECTION 136).

A complete, dependency-free implementation of the graph storage port used for
tests and offline development. Production deployments swap in a Graphiti/FalkorDB
adapter behind the same port without changing the Graph Engine.
"""

from __future__ import annotations

from collections import defaultdict

from ecms.graph.domain.graph import GraphEdge, GraphNode

__all__ = ["InMemoryGraphStore"]


class InMemoryGraphStore:
    """An in-memory adjacency-indexed graph store (SECTION 136)."""

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._outgoing: dict[str, set[str]] = defaultdict(set)
        self._incoming: dict[str, set[str]] = defaultdict(set)

    async def upsert_node(self, node: GraphNode) -> None:
        """Insert or replace a node."""
        self._nodes[node.node_id] = node

    async def get_node(self, node_id: str) -> GraphNode | None:
        """Return a node by id, or ``None``."""
        return self._nodes.get(node_id)

    async def delete_node(self, node_id: str) -> None:
        """Remove a node and every edge incident to it."""
        self._nodes.pop(node_id, None)
        for edge_id in self._outgoing.pop(node_id, set()) | self._incoming.pop(node_id, set()):
            await self.delete_edge(edge_id)

    async def upsert_edge(self, edge: GraphEdge) -> None:
        """Insert or replace an edge and update the adjacency indexes."""
        self._edges[edge.edge_id] = edge
        self._outgoing[edge.source].add(edge.edge_id)
        self._incoming[edge.target].add(edge.edge_id)

    async def delete_edge(self, edge_id: str) -> None:
        """Remove an edge by id."""
        edge = self._edges.pop(edge_id, None)
        if edge is not None:
            self._outgoing[edge.source].discard(edge_id)
            self._incoming[edge.target].discard(edge_id)

    async def edges_of(self, node_id: str) -> list[GraphEdge]:
        """Return all edges incident to a node."""
        edge_ids = self._outgoing.get(node_id, set()) | self._incoming.get(node_id, set())
        return [self._edges[edge_id] for edge_id in edge_ids]

    async def neighbors(self, node_id: str) -> list[GraphNode]:
        """Return the nodes adjacent to a node (in either direction)."""
        neighbor_ids: set[str] = set()
        for edge_id in self._outgoing.get(node_id, set()):
            neighbor_ids.add(self._edges[edge_id].target)
        for edge_id in self._incoming.get(node_id, set()):
            neighbor_ids.add(self._edges[edge_id].source)
        return [
            self._nodes[neighbor_id] for neighbor_id in neighbor_ids if neighbor_id in self._nodes
        ]

    async def all_nodes(self) -> list[GraphNode]:
        """Return every node."""
        return list(self._nodes.values())

    async def all_edges(self) -> list[GraphEdge]:
        """Return every edge."""
        return list(self._edges.values())
