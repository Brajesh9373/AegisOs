"""FalkorDB-backed graph store implementing the GraphStore protocol.

Uses the falkordb-py client with raw Cypher queries.
Node label: :Node  |  Edge label: :Edge

All sync falkordb calls are wrapped in asyncio.to_thread for non-blocking async.
"""

from __future__ import annotations

import asyncio
import json
from urllib.parse import urlparse

from ecms.graph.domain.graph import GraphEdge, GraphNode
from ecms.shared.ids import new_id

__all__ = ["FalkorDBCypherStore"]


def _parse_redis_url(url: str) -> tuple[str, int]:
    parsed = urlparse(url)
    return parsed.hostname or "localhost", parsed.port or 6379


def _node_from_result(row: list) -> GraphNode:
    """Hydrate a GraphNode from a raw FalkorDB result row."""
    n = row[0]
    props = n.properties
    return GraphNode(
        node_id=props.get("node_id", n.id if hasattr(n, "id") else ""),
        ontology_type=props.get("ontology_type", "unknown"),
        display_name=props.get("display_name", ""),
        canonical_name=props.get("canonical_name", ""),
        confidence=int(props.get("confidence", 0)),
        importance=int(props.get("importance", 0)),
        version=int(props.get("version", 1)),
        properties=json.loads(props.get("properties", "{}")),
    )


def _edge_from_result(row: list) -> GraphEdge:
    """Hydrate a GraphEdge from a raw FalkorDB result row.

    Result row shape depends on query, but typically: [edge, source_id, target_id]
    """
    e = row[0]
    props = e.properties
    src = e.src_node.properties.get("node_id", "") if hasattr(e, "src_node") else ""
    tgt = e.dest_node.properties.get("node_id", "") if hasattr(e, "dest_node") else ""
    return GraphEdge(
        edge_id=props.get("edge_id", new_id("edge")),
        source=props.get("source", src),
        target=props.get("target", tgt),
        relationship_type=props.get("relationship_type", "unknown"),
        weight=float(props.get("weight", 1.0)),
        confidence=int(props.get("confidence", 0)),
        version=int(props.get("version", 1)),
        properties=json.loads(props.get("properties", "{}")),
    )


class FalkorDBCypherStore:
    """FalkorDB-backed graph store implementing the GraphStore protocol."""

    def __init__(
        self,
        url: str = "redis://localhost:6379",
        graph_name: str = "ecms",
    ) -> None:
        import falkordb

        host, port = _parse_redis_url(url)
        self._db = falkordb.FalkorDB(host=host, port=port)
        self._graph = self._db.select_graph(graph_name)
        self._graph_name = graph_name
        # Connectivity check: raises if FalkorDB module not loaded on this Redis
        self._graph.query("RETURN 1")
        # Ensure indices for fast lookups
        try:
            self._graph.query("CREATE INDEX FOR (n:Node) ON (n.node_id)")
        except Exception:
            pass
        try:
            self._graph.query("CREATE INDEX FOR ()-[e:Edge]-() ON (e.edge_id)")
        except Exception:
            pass

    # ── Node operations ──────────────────────────────────────────────

    async def upsert_node(self, node: GraphNode) -> None:
        await asyncio.to_thread(
            self._graph.query,
            """MERGE (n:Node {node_id: $node_id})
               SET n.ontology_type = $ontology_type,
                   n.display_name = $display_name,
                   n.canonical_name = $canonical_name,
                   n.confidence = $confidence,
                   n.importance = $importance,
                   n.version = $version,
                   n.properties = $properties""",
            {
                "node_id": node.node_id,
                "ontology_type": node.ontology_type,
                "display_name": node.display_name,
                "canonical_name": node.canonical_name,
                "confidence": node.confidence,
                "importance": node.importance,
                "version": node.version,
                "properties": json.dumps(node.properties),
            },
        )

    async def get_node(self, node_id: str) -> GraphNode | None:
        result = await asyncio.to_thread(
            self._graph.query,
            "MATCH (n:Node {node_id: $node_id}) RETURN n",
            {"node_id": node_id},
        )
        if result.result_set:
            return _node_from_result(result.result_set[0])
        return None

    async def delete_node(self, node_id: str) -> None:
        await asyncio.to_thread(
            self._graph.query,
            "MATCH (n:Node {node_id: $node_id}) DETACH DELETE n",
            {"node_id": node_id},
        )

    async def all_nodes(self) -> list[GraphNode]:
        result = await asyncio.to_thread(
            self._graph.query, "MATCH (n:Node) RETURN n ORDER BY n.display_name"
        )
        return [_node_from_result(row) for row in result.result_set]

    # ── Edge operations ──────────────────────────────────────────────

    async def upsert_edge(self, edge: GraphEdge) -> None:
        await asyncio.to_thread(
            self._graph.query,
            """MATCH (s:Node {node_id: $source})
               MATCH (t:Node {node_id: $target})
               MERGE (s)-[e:Edge {edge_id: $edge_id}]->(t)
               SET e.relationship_type = $relationship_type,
                   e.weight = $weight,
                   e.confidence = $confidence,
                   e.version = $version,
                   e.properties = $properties,
                   e.source = $source,
                   e.target = $target""",
            {
                "edge_id": edge.edge_id,
                "source": edge.source,
                "target": edge.target,
                "relationship_type": edge.relationship_type,
                "weight": edge.weight,
                "confidence": edge.confidence,
                "version": edge.version,
                "properties": json.dumps(edge.properties),
            },
        )

    async def delete_edge(self, edge_id: str) -> None:
        await asyncio.to_thread(
            self._graph.query,
            "MATCH ()-[e:Edge {edge_id: $edge_id}]->() DELETE e",
            {"edge_id": edge_id},
        )

    async def edges_of(self, node_id: str) -> list[GraphEdge]:
        result = await asyncio.to_thread(
            self._graph.query,
            """MATCH (n:Node {node_id: $node_id})-[e:Edge]-(:Node)
               RETURN e, startNode(e).node_id, endNode(e).node_id""",
            {"node_id": node_id},
        )
        edges: list[GraphEdge] = []
        for row in result.result_set:
            e = row[0]
            props = e.properties
            edges.append(
                GraphEdge(
                    edge_id=props.get("edge_id", new_id("edge")),
                    source=props.get("source", row[1] if len(row) > 1 else ""),
                    target=props.get("target", row[2] if len(row) > 2 else ""),
                    relationship_type=props.get("relationship_type", "unknown"),
                    weight=float(props.get("weight", 1.0)),
                    confidence=int(props.get("confidence", 0)),
                    version=int(props.get("version", 1)),
                    properties=json.loads(props.get("properties", "{}")),
                )
            )
        return edges

    async def neighbors(self, node_id: str) -> list[GraphNode]:
        result = await asyncio.to_thread(
            self._graph.query,
            "MATCH (n:Node {node_id: $node_id})-[e:Edge]-(nb:Node) RETURN DISTINCT nb",
            {"node_id": node_id},
        )
        return [_node_from_result(row) for row in result.result_set]

    async def all_edges(self) -> list[GraphEdge]:
        result = await asyncio.to_thread(
            self._graph.query, "MATCH ()-[e:Edge]->() RETURN e"
        )
        edges: list[GraphEdge] = []
        for row in result.result_set:
            e = row[0]
            props = e.properties
            edges.append(
                GraphEdge(
                    edge_id=props.get("edge_id", new_id("edge")),
                    source=props.get("source", ""),
                    target=props.get("target", ""),
                    relationship_type=props.get("relationship_type", "unknown"),
                    weight=float(props.get("weight", 1.0)),
                    confidence=int(props.get("confidence", 0)),
                    version=int(props.get("version", 1)),
                    properties=json.loads(props.get("properties", "{}")),
                )
            )
        return edges

    # ── Search ───────────────────────────────────────────────────────

    async def search_nodes(self, query: str, *, limit: int = 20) -> list[GraphNode]:
        """Full-text search on display_name and canonical_name."""
        result = await asyncio.to_thread(
            self._graph.query,
            """MATCH (n:Node)
               WHERE n.display_name CONTAINS $query
                  OR n.canonical_name CONTAINS $query
               RETURN n
               LIMIT $limit""",
            {"query": query, "limit": limit},
        )
        return [_node_from_result(row) for row in result.result_set]
