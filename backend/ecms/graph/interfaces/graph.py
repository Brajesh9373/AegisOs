"""Graph storage port (SECTION 76/136).

The Graph Engine operates entirely through this port; the concrete backend
(in-memory for tests, Graphiti over FalkorDB in production) is replaceable. No
subsystem talks to the persistence backend directly.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ecms.graph.domain.graph import GraphEdge, GraphNode

__all__ = ["GraphStore"]


@runtime_checkable
class GraphStore(Protocol):
    """Persistence port for the enterprise cognitive graph (SECTION 136).

    Operations:
        upsert_node: Insert or replace a node.
        get_node: Return a node by id, or ``None``.
        delete_node: Remove a node and its incident edges.
        upsert_edge: Insert or replace an edge.
        delete_edge: Remove an edge by id.
        edges_of: Return all edges incident to a node.
        neighbors: Return the nodes adjacent to a node.
        all_nodes: Return every node.
        all_edges: Return every edge.
    """

    async def upsert_node(self, node: GraphNode) -> None: ...
    async def get_node(self, node_id: str) -> GraphNode | None: ...
    async def delete_node(self, node_id: str) -> None: ...
    async def upsert_edge(self, edge: GraphEdge) -> None: ...
    async def delete_edge(self, edge_id: str) -> None: ...
    async def edges_of(self, node_id: str) -> list[GraphEdge]: ...
    async def neighbors(self, node_id: str) -> list[GraphNode]: ...
    async def all_nodes(self) -> list[GraphNode]: ...
    async def all_edges(self) -> list[GraphEdge]: ...
