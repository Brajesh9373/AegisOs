"""Graph event factories (SECTION 58).

Every mutation of the cognitive graph emits an immutable event in the GRAPH
category so the graph's evolution is fully auditable and replayable.
"""

from __future__ import annotations

from typing import Any

from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent, make_event

__all__ = [
    "node_created",
    "node_deleted",
    "node_updated",
    "relationship_created",
    "relationship_deleted",
]

_PRODUCER = "graph-engine"


def _event(event_type: str, payload: dict[str, Any]) -> BaseEvent:
    return make_event(event_type, EventCategory.GRAPH, _PRODUCER, payload=payload)


def node_created(
    node_id: str,
    *,
    display_name: str = "",
    ontology_type: str = "unknown",
    confidence: int = 0,
    importance: int = 0,
) -> BaseEvent:
    """Emitted when a node is created (SECTION 58)."""
    return _event(
        "NodeCreated",
        {
            "node_id": node_id,
            "display_name": display_name,
            "ontology_type": ontology_type,
            "confidence": confidence,
            "importance": importance,
        },
    )


def node_updated(
    node_id: str,
    *,
    display_name: str = "",
    ontology_type: str = "unknown",
    confidence: int = 0,
    importance: int = 0,
) -> BaseEvent:
    """Emitted when a node is updated to a new version (SECTION 58)."""
    return _event(
        "NodeUpdated",
        {
            "node_id": node_id,
            "display_name": display_name,
            "ontology_type": ontology_type,
            "confidence": confidence,
            "importance": importance,
        },
    )


def node_deleted(node_id: str) -> BaseEvent:
    """Emitted when a node is deleted (SECTION 58)."""
    return _event("NodeDeleted", {"node_id": node_id})


def relationship_created(
    edge_id: str,
    source: str = "",
    target: str = "",
    relationship_type: str = "unknown",
    weight: float = 1.0,
    confidence: int = 0,
) -> BaseEvent:
    """Emitted when a relationship is created (SECTION 58)."""
    return _event(
        "RelationshipCreated",
        {
            "edge_id": edge_id,
            "source": source,
            "target": target,
            "relationship_type": relationship_type,
            "weight": weight,
            "confidence": confidence,
        },
    )


def relationship_deleted(edge_id: str) -> BaseEvent:
    """Emitted when a relationship is deleted (SECTION 58)."""
    return _event("RelationshipDeleted", {"edge_id": edge_id})
