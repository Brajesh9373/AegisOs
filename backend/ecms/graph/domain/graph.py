"""Enterprise cognitive graph domain models (SECTION 137/138/143).

There is only one graph. Nodes project cognitive objects and edges project
relationships. A :class:`Subgraph` is a *projection* of the single graph (a graph
view), never a separate copy of the data.
"""

from __future__ import annotations

import hashlib
from typing import Any

from pydantic import Field

from ecms.shared.ids import new_id
from ecms.shared.models.base import DomainModel

__all__ = ["GraphEdge", "GraphNode", "Subgraph"]


def _edge_id() -> str:
    return new_id("edge")


def deterministic_edge_id(source: str, target: str, relationship_type: str) -> str:
    """Generate a deterministic edge_id from source+target+type for idempotent upserts."""
    h = hashlib.sha256(f"{source}|{target}|{relationship_type}".encode()).hexdigest()[:12]
    return f"edge-{h}"


class GraphNode(DomainModel):
    """A graph node projecting one cognitive object (SECTION 137)."""

    node_id: str
    ontology_type: str
    display_name: str
    canonical_name: str
    confidence: int = Field(default=0, ge=0, le=100)
    importance: int = Field(default=0, ge=0, le=100)
    version: int = Field(default=1, ge=1)
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(DomainModel):
    """A graph edge projecting one relationship (SECTION 138)."""

    edge_id: str = Field(default_factory=_edge_id)
    source: str
    target: str
    relationship_type: str
    weight: float = Field(default=1.0, ge=0.0)
    confidence: int = Field(default=0, ge=0, le=100)
    version: int = Field(default=1, ge=1)
    properties: dict[str, Any] = Field(default_factory=dict)


class Subgraph(DomainModel):
    """A projection of the one graph: nodes and the edges among them (SECTION 143)."""

    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
