"""Tests for the graph engine and traversal algorithms (SECTION 76/143-146)."""

from __future__ import annotations

from ecms.events import InMemoryEventBus
from ecms.graph import GraphEngine
from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent
from ecms.shared.models import UniversalCognitiveObject


def _uco(name: str, ontology_type: str = "component") -> UniversalCognitiveObject:
    return UniversalCognitiveObject(
        canonical_name=name,
        display_name=name,
        ontology_type=ontology_type,
        description=f"{name} description",
    )


async def _line_graph() -> tuple[GraphEngine, list[str]]:
    engine = GraphEngine()
    nodes = [await engine.upsert_uco(_uco(name)) for name in ("A", "B", "C", "D")]
    ids = [node.node_id for node in nodes]
    await engine.create_relationship(ids[0], ids[1], "depends_on")
    await engine.create_relationship(ids[1], ids[2], "calls")
    await engine.create_relationship(ids[0], ids[3], "uses")
    return engine, ids


async def test_upsert_uco_versions_on_update() -> None:
    engine = GraphEngine()
    uco = _uco("Widget")
    first = await engine.upsert_uco(uco)
    assert first.version == 1
    second = await engine.upsert_uco(uco)
    assert second.version == 2


async def test_neighbors_and_shortest_path() -> None:
    engine, ids = await _line_graph()
    neighbor_ids = {node.node_id for node in await engine.neighbors(ids[0])}
    assert neighbor_ids == {ids[1], ids[3]}
    path = await engine.shortest_path(ids[0], ids[2])
    assert path == [ids[0], ids[1], ids[2]]


async def test_shortest_path_returns_empty_when_unreachable() -> None:
    engine, ids = await _line_graph()
    isolated = await engine.upsert_uco(_uco("Z"))
    assert await engine.shortest_path(ids[0], isolated.node_id) == []


async def test_expand_collects_neighborhood() -> None:
    engine, ids = await _line_graph()
    subgraph = await engine.expand(ids[0], hops=1)
    node_ids = {node.node_id for node in subgraph.nodes}
    assert ids[0] in node_ids
    assert ids[1] in node_ids
    assert ids[3] in node_ids
    assert ids[2] not in node_ids


async def test_view_projects_by_ontology_type() -> None:
    engine = GraphEngine()
    api = await engine.upsert_uco(_uco("Health", "api"))
    await engine.upsert_uco(_uco("Widget", "component"))
    view = await engine.view(ontology_type="api")
    assert [node.node_id for node in view.nodes] == [api.node_id]


async def test_statistics_reports_counts_and_density() -> None:
    engine, _ = await _line_graph()
    stats = await engine.statistics()
    assert stats["node_count"] == 4
    assert stats["edge_count"] == 3
    assert 0.0 < stats["density"] <= 1.0


async def test_delete_node_removes_incident_edges() -> None:
    engine, ids = await _line_graph()
    await engine.delete_node(ids[1])
    assert await engine.find_node(ids[1]) is None
    assert await engine.shortest_path(ids[0], ids[2]) == []


async def test_graph_mutations_emit_events() -> None:
    bus = InMemoryEventBus()
    seen: list[str] = []

    async def handler(event: BaseEvent) -> None:
        seen.append(event.event_type)

    bus.subscribe(handler, category=EventCategory.GRAPH)
    engine = GraphEngine(event_bus=bus)
    node = await engine.upsert_uco(_uco("A"))
    other = await engine.upsert_uco(_uco("B"))
    await engine.create_relationship(node.node_id, other.node_id, "uses")
    await engine.delete_node(node.node_id)
    assert "NodeCreated" in seen
    assert "RelationshipCreated" in seen
    assert "NodeDeleted" in seen
