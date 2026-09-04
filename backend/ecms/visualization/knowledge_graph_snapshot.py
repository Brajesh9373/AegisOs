"""Deterministic Apache Arrow contracts for knowledge graph snapshots."""

from __future__ import annotations

import hashlib
import io
import math
import re
from dataclasses import dataclass
from typing import Any

import pyarrow as pa
import pyarrow.ipc as ipc

SCHEMA_VERSION = 1

POINTS_SCHEMA = pa.schema(
    [
        pa.field("index", pa.int32(), nullable=False),
        pa.field("id", pa.string(), nullable=False),
        pa.field("label", pa.string(), nullable=False),
        pa.field("group", pa.string(), nullable=False),
        pa.field("category", pa.string(), nullable=False),
        pa.field("source_group", pa.string(), nullable=True),
        pa.field("confidence", pa.float32(), nullable=False),
        pa.field("x", pa.float32(), nullable=False),
        pa.field("y", pa.float32(), nullable=False),
    ],
    metadata={b"ecms.schema": b"knowledge-graph-points", b"ecms.version": b"1"},
)

LINKS_SCHEMA = pa.schema(
    [
        pa.field("index", pa.int32(), nullable=False),
        pa.field("id", pa.string(), nullable=False),
        pa.field("source", pa.int32(), nullable=False),
        pa.field("target", pa.int32(), nullable=False),
        pa.field("label", pa.string(), nullable=False),
    ],
    metadata={b"ecms.schema": b"knowledge-graph-links", b"ecms.version": b"1"},
)


@dataclass(frozen=True)
class ArrowArtifact:
    """One immutable serialized Arrow file."""

    data: bytes
    checksum: str
    row_count: int


@dataclass(frozen=True)
class KnowledgeGraphArtifacts:
    """Point and link artifacts sharing one stable node-index mapping."""

    points: ArrowArtifact
    links: ArrowArtifact


def _serialize(table: pa.Table) -> ArrowArtifact:
    target = io.BytesIO()
    with ipc.new_file(target, table.schema) as writer:
        writer.write_table(table)
    data = target.getvalue()
    return ArrowArtifact(
        data=data,
        checksum=hashlib.sha256(data).hexdigest(),
        row_count=table.num_rows,
    )


def _position(
    node_id: str,
    source_group: str | None,
    index: int,
    count: int,
    degree: int,
    max_degree: int,
    *,
    is_root: bool = False,
    is_source_hub: bool = False,
) -> tuple[float, float]:
    if is_root:
        return (0.0, 0.0)
    node_digest = hashlib.sha256(node_id.encode()).digest()
    node_jitter = int.from_bytes(node_digest[:4], "big") / (2**32)
    if is_source_hub:
        angle = node_jitter * math.tau
        return (math.cos(angle) * 150, math.sin(angle) * 150)

    # A golden-angle disc recreates the previous dense, centered knowledge
    # sphere without running a browser force simulation. Highly connected
    # nodes move toward the core while a small source bias preserves structure.
    golden_angle = math.pi * (3 - math.sqrt(5))
    angle = index * golden_angle + node_jitter * 0.42
    source_digest = hashlib.sha256((source_group or "unscoped").encode()).digest()
    source_angle = int.from_bytes(source_digest[:4], "big") / (2**32) * math.tau
    angle = angle * 0.88 + source_angle * 0.12
    radial_rank = math.sqrt((index + 1) / max(count, 1))
    degree_strength = math.log1p(degree) / max(math.log1p(max_degree), 1)
    radius = (80 + radial_rank * 1_440) * (1 - degree_strength * 0.58)
    radial_jitter = 0.92 + (node_digest[4] / 255) * 0.16
    return (
        math.cos(angle) * radius * radial_jitter,
        math.sin(angle) * radius * radial_jitter,
    )


def _with_source_hierarchy(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Restore the source/containment structure used by the previous overview."""
    augmented_nodes = [dict(node) for node in nodes]
    augmented_edges = [dict(edge) for edge in edges]
    existing_ids = {str(node["id"]) for node in augmented_nodes}
    source_members: dict[str, list[str]] = {}
    source_labels: dict[str, str] = {}
    for node in augmented_nodes:
        source_group = str(node.get("source_group") or "")
        if not source_group:
            continue
        source_url = str(node.get("source_url") or "").rstrip("/")
        if re.fullmatch(r"connection:\d+", source_group):
            hierarchy_key = source_group
            label = source_group.replace("connection:", "Connection ")
        elif source_url:
            provider = source_group.split(":", 1)[0].lower()
            hierarchy_key = f"{provider}:{source_url.lower()}"
            repo_parts = source_url.removesuffix(".git").split("/")
            repo_name = "/".join(repo_parts[-2:]) if len(repo_parts) > 1 else source_url
            label = repo_name or provider.upper()
        else:
            provider = source_group.split(":", 1)[0].lower()
            hierarchy_key = f"{provider}:unscoped"
            label = f"{provider.upper()} source"
        source_members.setdefault(hierarchy_key, []).append(str(node["id"]))
        source_labels[hierarchy_key] = label

    if not source_members:
        return augmented_nodes, augmented_edges

    root_id = "knowledge-source:root"
    if root_id not in existing_ids:
        augmented_nodes.append(
            {
                "id": root_id,
                "label": "Knowledge Sources",
                "group": "connection",
                "category": "infrastructure",
                "node_confidence": 1.0,
                "_layout_role": "root",
            }
        )
        existing_ids.add(root_id)

    for source_group in sorted(source_members):
        hub_id = (
            source_group
            if re.fullmatch(r"connection:\d+", source_group)
            else "knowledge-source:" + hashlib.sha256(source_group.encode()).hexdigest()[:16]
        )
        if hub_id not in existing_ids:
            augmented_nodes.append(
                {
                    "id": hub_id,
                    "label": source_labels[source_group],
                    "group": "repository",
                    "category": "infrastructure",
                    "source_group": source_group,
                    "node_confidence": 1.0,
                    "_layout_role": "source_hub",
                }
            )
            existing_ids.add(hub_id)
        augmented_edges.append(
            {
                "id": f"source-root:{source_group}",
                "source": root_id,
                "target": hub_id,
                "label": "indexes",
            }
        )
        for node_id in source_members[source_group]:
            augmented_edges.append(
                {
                    "id": f"source-contains:{source_group}:{node_id}",
                    "source": hub_id,
                    "target": node_id,
                    "label": "contains",
                }
            )
    return augmented_nodes, augmented_edges


def build_arrow_artifacts(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> KnowledgeGraphArtifacts:
    """Build deterministic Arrow files and reject invalid graph relationships."""
    nodes, edges = _with_source_hierarchy(nodes, edges)
    ordered_nodes = sorted(nodes, key=lambda item: str(item["id"]))
    ids = [str(node["id"]) for node in ordered_nodes]
    if len(ids) != len(set(ids)):
        raise ValueError("knowledge graph contains duplicate node IDs")
    index_by_id = {node_id: index for index, node_id in enumerate(ids)}

    normalized_edges: list[tuple[str, str, str, str]] = []
    degree_by_id = dict.fromkeys(ids, 0)
    for edge in edges:
        source = str(edge.get("from_") or edge.get("source") or "")
        target = str(edge.get("to") or edge.get("target") or "")
        if source not in index_by_id or target not in index_by_id:
            raise ValueError(f"edge references missing endpoint: {source!r} -> {target!r}")
        edge_id = str(edge.get("id") or f"{source}:{target}:{edge.get('label', 'related')}")
        normalized_edges.append(
            (edge_id, source, target, str(edge.get("label") or edge.get("type") or "related"))
        )
        degree_by_id[source] += 1
        degree_by_id[target] += 1
    normalized_edges.sort()
    max_degree = max(degree_by_id.values(), default=1)

    point_rows: list[dict[str, Any]] = []
    for index, node in enumerate(ordered_nodes):
        source_group = node.get("source_group")
        layout_role = node.get("_layout_role")
        x, y = _position(
            ids[index],
            str(source_group) if source_group else None,
            index,
            len(ordered_nodes),
            degree_by_id[ids[index]],
            max_degree,
            is_root=layout_role == "root",
            is_source_hub=layout_role == "source_hub",
        )
        point_rows.append(
            {
                "index": index,
                "id": ids[index],
                "label": str(node.get("label") or ids[index]),
                "group": str(node.get("group") or node.get("type") or "unknown"),
                "category": str(node.get("domain") or node.get("category") or "other"),
                "source_group": str(source_group) if source_group else None,
                "confidence": float(node.get("node_confidence") or 0.5),
                "x": x,
                "y": y,
            }
        )
    link_rows = [
        {
            "index": index,
            "id": edge_id,
            "source": index_by_id[source],
            "target": index_by_id[target],
            "label": label,
        }
        for index, (edge_id, source, target, label) in enumerate(normalized_edges)
    ]

    points_table = pa.Table.from_pylist(point_rows, schema=POINTS_SCHEMA)
    links_table = pa.Table.from_pylist(link_rows, schema=LINKS_SCHEMA)
    return KnowledgeGraphArtifacts(
        points=_serialize(points_table),
        links=_serialize(links_table),
    )


def read_and_validate_artifact(data: bytes, expected_schema: pa.Schema) -> pa.Table:
    """Read an Arrow file and enforce the exact versioned schema."""
    try:
        table = ipc.open_file(pa.BufferReader(data)).read_all()
    except (pa.ArrowInvalid, OSError) as exc:
        raise ValueError("invalid Arrow snapshot") from exc
    if table.schema != expected_schema:
        raise ValueError("unexpected Arrow snapshot schema")
    return table
