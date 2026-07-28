"""Cognition REST routes (SECTION 193).

Exposes the cognitive pipeline over REST: ingest information, search knowledge,
execute a prompt through the runtime kernel, and read graph statistics. Every
route delegates to the Kernel API assembly - the API never touches engines
directly.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ecms.sdk.cognitive import CognitiveSystem
from ecms.shared.models import UniversalKnowledgeObject

__all__ = ["router"]

router = APIRouter(tags=["cognition"])

# ── Provider sync moved to legacy /providers/git/sync ──────────────────
# The legacy GitProvider + PipelineOrchestrator (at /providers/git/sync)
# provides full structural/semantic extraction with workspace scoping.
# See legacy_ecms.api.routes.providers for the complete implementation.


class ExecuteRequest(BaseModel):
    """Request body for executing a prompt through the runtime kernel."""

    prompt: str
    organization_id: str = "default"
    user_id: str = "system"


class IngestRequest(BaseModel):
    """Request body for ingesting information into the knowledge engine."""

    title: str
    content: str
    provider: str = "manual"
    language: str = "python"
    organization_id: str = "default"


def _system(request: Request) -> CognitiveSystem:
    system: CognitiveSystem = request.app.state.cognitive
    return system


@router.post("/execute")
async def execute(body: ExecuteRequest, request: Request) -> dict[str, Any]:
    """Run the full cognitive pipeline for a prompt (SECTION 92)."""
    result = await _system(request).kernel.execute(
        body.prompt,
        organization_id=body.organization_id,
        user_id=body.user_id,
    )
    return result.model_dump()


@router.post("/knowledge/ingest")
async def ingest(body: IngestRequest, request: Request) -> dict[str, Any]:
    """Ingest information as a UKO and return the generated cognitive objects."""
    uko = UniversalKnowledgeObject(
        provider=body.provider,
        provider_object_type="file",
        provider_object_id=body.title,
        organization_id=body.organization_id,
        title=body.title,
        raw_content=body.content,
        language=body.language,
    )
    ucos = await _system(request).knowledge.ingest(uko)
    return {"generated": len(ucos), "uco_ids": [uco.uco_id for uco in ucos]}


@router.get("/knowledge/search")
async def search(request: Request, q: str, limit: int = 10) -> dict[str, Any]:
    """Return cognitive objects matching a query."""
    results = await _system(request).knowledge.search(q, limit=limit)
    return {
        "results": [
            {
                "uco_id": uco.uco_id,
                "name": uco.display_name,
                "ontology_type": uco.ontology_type,
            }
            for uco in results
        ]
    }


@router.get("/graph/statistics")
async def graph_statistics(request: Request) -> dict[str, Any]:
    """Return statistics for the enterprise cognitive graph (SECTION 146)."""
    return await _system(request).graph.statistics()


@router.get("/graph/nodes")
async def graph_nodes(
    request: Request,
    page: int = 1,
    size: int = 50,
    ontology_type: str | None = None,
) -> dict[str, Any]:
    """Return paginated graph nodes, optionally filtered by ontology_type."""
    graph = _system(request).graph
    all_nodes = await graph._store.all_nodes()
    if ontology_type:
        all_nodes = [n for n in all_nodes if n.ontology_type == ontology_type]
    total = len(all_nodes)
    start = (page - 1) * size
    paged = all_nodes[start : start + size]
    return {
        "nodes": [n.model_dump() for n in paged],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/graph/edges")
async def graph_edges(
    request: Request,
    page: int = 1,
    size: int = 50,
    relationship_type: str | None = None,
) -> dict[str, Any]:
    """Return paginated graph edges, optionally filtered by relationship_type."""
    graph = _system(request).graph
    all_edges = await graph._store.all_edges()
    if relationship_type:
        all_edges = [e for e in all_edges if e.relationship_type == relationship_type]
    total = len(all_edges)
    start = (page - 1) * size
    paged = all_edges[start : start + size]
    return {
        "edges": [
            {
                **e.model_dump(),
                "source_name": (await graph.find_node(e.source)).display_name if (await graph.find_node(e.source)) else e.source,
                "target_name": (await graph.find_node(e.target)).display_name if (await graph.find_node(e.target)) else e.target,
            }
            for e in paged
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/graph/node/{node_id}")
async def graph_node_detail(node_id: str, request: Request) -> dict[str, Any]:
    """Return a single node and all edges incident to it."""
    graph = _system(request).graph
    node = await graph.find_node(node_id)
    if node is None:
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "not_found"}, status_code=404)
    edges = await graph._store.edges_of(node_id)
    return {
        "node": node.model_dump(),
        "edges": [
            {
                **e.model_dump(),
                "source_name": (await graph.find_node(e.source)).display_name if (await graph.find_node(e.source)) else e.source,
                "target_name": (await graph.find_node(e.target)).display_name if (await graph.find_node(e.target)) else e.target,
            }
            for e in edges
        ],
    }


@router.get("/graph/expand/{node_id}")
async def graph_expand(node_id: str, request: Request, hops: int = 1) -> dict[str, Any]:
    """Return the subgraph within `hops` hops of a node."""
    graph = _system(request).graph
    node = await graph.find_node(node_id)
    if node is None:
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "not_found"}, status_code=404)
    subgraph = await graph.expand(node_id, max_hops=hops)
    return subgraph.model_dump()


@router.get("/graph/search")
async def graph_search(request: Request, q: str, limit: int = 20) -> dict[str, Any]:
    """Search graph nodes by display_name or canonical_name."""
    graph = _system(request).graph
    store = graph._store
    if hasattr(store, "search_nodes"):
        results = await store.search_nodes(q, limit=limit)  # type: ignore[attr-defined]
    else:
        all_nodes = await store.all_nodes()
        query_lower = q.lower()
        results = [
            n for n in all_nodes
            if query_lower in n.display_name.lower() or query_lower in n.canonical_name.lower()
        ][:limit]
    return {"results": [n.model_dump() for n in results]}
