"""Workspace management endpoints — create, list, and delete workspaces."""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from legacy_ecms.api.graph_context import create_graph_client
from legacy_ecms.pipeline.workspace import persist_workspace_node
from ecms.visualization.graph_changed import graph_changed

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
logger = logging.getLogger("ecms.workspaces")


class CreateWorkspaceRequest(BaseModel):
    workspace_id: str = Field(min_length=1, max_length=128)
    name: str | None = None


class WorkspaceInfo(BaseModel):
    workspace_id: str
    created: bool


@router.post("", response_model=WorkspaceInfo)
async def create_workspace(request: CreateWorkspaceRequest) -> WorkspaceInfo:
    import falkordb
    from legacy_ecms.config import get_settings
    from legacy_ecms.core.graph import GraphClient

    settings = get_settings()
    graph = GraphClient(settings)
    graph._raw_mode = True
    try:
        db = falkordb.FalkorDB(
            host=settings.falkordb_host, port=settings.falkordb_port,
            password=settings.falkordb_password or None)
        graph._raw_graph = db.select_graph(settings.falkordb_database)
        await persist_workspace_node(graph, request.workspace_id, request.name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        await graph_changed(
            "default",
            source="workspace",
            revision=request.workspace_id,
        )
    except Exception as exc:
        logger.warning("workspace snapshot trigger failed: %s", exc)

    # Also persist project metadata in PostgreSQL
    try:
        from ecms.persistence.database.rest_session import db_session
        from ecms.persistence.repositories.project import ProjectRepository
        async with db_session() as session:
            repo = ProjectRepository(session)
            await repo.upsert(
                project_id=f"proj:{request.workspace_id}",
                workspace_id=request.workspace_id,
                name=request.name or request.workspace_id,
                group_id=request.workspace_id,
            )
    except Exception:
        pass  # DB is optional — graph is required

    return WorkspaceInfo(workspace_id=request.workspace_id, created=True)


@router.get("/{workspace_id}/graph")
async def get_workspace_graph(workspace_id: str) -> dict:
    """Get all UKOs and edges scoped to a specific workspace."""
    import falkordb
    from legacy_ecms.config import get_settings

    settings = get_settings()
    db = falkordb.FalkorDB(
        host=settings.falkordb_host, port=settings.falkordb_port,
        password=settings.falkordb_password or None)
    g = db.select_graph(settings.falkordb_database)

    ws_node_id = f"workspace:{workspace_id}"
    try:
        result = g.query(
            "MATCH (w:UKO {id: $ws_id}) "
            "MATCH (u:UKO)-[r:RELATES {label: 'part_of_workspace'}]->(w) "
            "OPTIONAL MATCH (u)-[r2:RELATES]->(t:UKO) "
            "RETURN u.id, u.name, u.type, u.layer, "
            "r2.label, t.id, t.name, t.type, r2.confidence, r2.extraction_method",
            {"ws_id": ws_node_id},
        )
    except Exception:
        result = g.query(
            "MATCH (w:UKO {id: $ws_id}) "
            "MATCH (u:UKO)-[r:RELATES {label: 'part_of_workspace'}]->(w) "
            "RETURN u.id, u.name, u.type, u.layer",
            {"ws_id": ws_node_id},
        )

    rows = result.result_set if hasattr(result, "result_set") else result
    nodes_map: dict[str, dict] = {}
    edges: list[dict] = []
    for row in rows:
        uid = str(row[0]) if row[0] else ""
        if uid and uid not in nodes_map:
            nodes_map[uid] = {
                "id": uid,
                "name": str(row[1]) if len(row) > 1 else "",
                "type": str(row[2]) if len(row) > 2 else "",
                "layer": str(row[3]) if len(row) > 3 else "",
            }
        if len(row) > 5 and row[4] and row[5]:
            edges.append({
                "from": uid,
                "label": str(row[4]),
                "to": str(row[5]),
                "confidence": float(row[8]) if len(row) > 8 and row[8] else None,
                "extraction_method": str(row[9]) if len(row) > 9 and row[9] else None,
            })

    return {
        "workspace_id": workspace_id,
        "node_count": len(nodes_map),
        "edge_count": len(edges),
        "nodes": list(nodes_map.values()),
        "edges": edges,
    }
