"""Project routes — list, delete, and manage workspace projects.

Now backed by PostgreSQL for project/connector metadata, with FalkorDB for
knowledge graph data (node counts, breakdowns, etc.). Delete cascades across
ALL stores: DB, FalkorDB, Mem0/Qdrant, Redis sessions, GBrain disk files.
"""

import json
import os
import shutil

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ecms.visualization.graph_changed import snapshot_after_graph_write

router = APIRouter(prefix="/projects", tags=["projects"])


class DeleteProjectRequest(BaseModel):
    workspace_id: str


class EditProjectRequest(BaseModel):
    workspace_id: str
    name: str | None = None


def _get_falkordb_graph():
    """Return a FalkorDB graph handle for the current config."""
    import falkordb
    from legacy_ecms.config import get_settings
    s = get_settings()
    db = falkordb.FalkorDB(
        host=s.falkordb_host, port=s.falkordb_port,
        password=s.falkordb_password or None,
    )
    return db.select_graph(s.falkordb_database)


def _graph_stats(g, ws_id: str, ws_name: str) -> tuple[int, int, int, dict[str, int]]:
    """Return (node_count, edge_count, total_all, breakdown) for a workspace."""
    node_count = 0
    edge_count = 0
    breakdown: dict[str, int] = {}
    total_all = 0
    try:
        cr = g.query(
            "MATCH (w:UKO {id: $ws_id}) "
            "MATCH (u:UKO)-[r:RELATES {label: 'part_of_workspace'}]->(w) "
            "RETURN count(u), count(r)",
            {"ws_id": ws_id},
        )
        if cr.result_set:
            row = cr.result_set[0]
            node_count = int(row[0]) if row[0] else 0
            edge_count = int(row[1]) if len(row) > 1 and row[1] else 0

        ar = g.query(
            "MATCH (u:UKO) WHERE u.group_id = $gid RETURN u.type, count(u)",
            {"gid": ws_name},
        )
        all_rows = ar.result_set if hasattr(ar, "result_set") else ar
        for r in all_rows:
            t = str(r[0])
            c = int(r[1]) if len(r) > 1 else 0
            if t not in ("episode", "workspace"):
                breakdown[t] = c
        total_all = sum(breakdown.values())
    except Exception:
        pass
    return node_count, edge_count, total_all, breakdown


@router.get("")
async def list_projects(request: Request) -> list[dict]:
    """Return all projects — PostgreSQL is source-of-truth, enriched with graph stats."""
    try:
        from ecms.persistence.database.rest_session import db_session as pg_session
        from ecms.persistence.repositories.project import ProjectRepository
        async with pg_session() as session:
            repo = ProjectRepository(session)
            db_projects = await repo.export_all()
    except Exception:
        db_projects = []

    # Map workspace_id → DB record for fast lookup
    db_map: dict[str, dict] = {p["project_id"]: p for p in db_projects}

    # Enrich with graph stats
    g = None
    try:
        g = _get_falkordb_graph()
        ws_result = g.query("MATCH (w:UKO) WHERE w.type = 'workspace' RETURN w.id, w.name")
        ws_rows = ws_result.result_set if hasattr(ws_result, "result_set") else ws_result
        graph_workspaces: dict[str, str] = {}  # ws_id → ws_name
        for row in ws_rows:
            if row[0]:
                ws_id = str(row[0])
                ws_name = str(row[1]) if len(row) > 1 and row[1] else ws_id.replace("workspace:", "")
                graph_workspaces[ws_id] = ws_name
    except Exception:
        graph_workspaces = {}

    # Detect connectors from UKO sources in the graph
    connector_sources: dict[str, list[str]] = {}
    if g is not None:
        try:
            for ws_name in {v for v in graph_workspaces.values()}:
                src_result = g.query(
                    "MATCH (u:UKO) WHERE u.group_id = $gid RETURN DISTINCT u.source, u.type",
                    {"gid": ws_name},
                )
                src_rows = src_result.result_set if hasattr(src_result, "result_set") else src_result
                seen: set[str] = set()
                conns: list[str] = []
                for sr in src_rows:
                    source = str(sr[0]).lower() if sr[0] else ""
                    ntype = str(sr[1]).lower() if len(sr) > 1 and sr[1] else ""
                    for c in ("git", "mysql", "jira", "slack", "confluence"):
                        if c in source or c in ntype:
                            if c not in seen:
                                conns.append(c)
                                seen.add(c)
                connector_sources[ws_name] = conns
        except Exception:
            pass

    projects: list[dict] = []
    seen_ws: set[str] = set()

    # First: projects from PostgreSQL
    for dbp in db_projects:
        ws_id = dbp["project_id"]
        ws_short = ws_id
        seen_ws.add(ws_short)

        ws_graph_id = f"workspace:{ws_id}"
        raw_graph_name = graph_workspaces.get(ws_graph_id, ws_short)
        if raw_graph_name.startswith("workspace:"):
            raw_graph_name = raw_graph_name.replace("workspace:", "")

        # Use the DB name if it differs from ws_id, otherwise fall back to ws_id
        display_name = dbp.get("name", ws_short)
        if display_name == ws_short and raw_graph_name != ws_short:
            display_name = raw_graph_name

        nc, ec, ta, bd = (0, 0, 0, {})
        if g is not None:
            nc, ec, ta, bd = _graph_stats(g, ws_graph_id, ws_id)

        projects.append({
            "workspace_id": ws_short,
            "name": display_name,
            "node_count": nc,
            "edge_count": ec,
            "total_nodes": ta,
            "breakdown": bd,
            "connectors": connector_sources.get(ws_id, []),
            "connector_configs": dbp.get("connectors", []),
            "created_at": dbp.get("created_at", ""),
            "group_id": dbp.get("group_id", ws_id),
        })

    # Second: orphan workspaces in FalkorDB but not in PostgreSQL
    for ws_graph_id, ws_name in graph_workspaces.items():
        ws_short = ws_name if not ws_name.startswith("workspace:") else ws_name.replace("workspace:", "")
        if ws_short in seen_ws:
            continue
        seen_ws.add(ws_short)

        nc, ec, ta, bd = _graph_stats(g, ws_graph_id, ws_name) if g is not None else (0, 0, 0, {})

        projects.append({
            "workspace_id": ws_short,
            "name": ws_name if not ws_name.startswith("workspace:") else ws_short,
            "node_count": nc,
            "edge_count": ec,
            "total_nodes": ta,
            "breakdown": bd,
            "connectors": connector_sources.get(ws_name, []),
            "connector_configs": [],
            "created_at": "",
        })

    return projects


@router.delete("/{workspace_id}")
async def delete_project(workspace_id: str) -> dict:
    """Full cascade delete across ALL stores for a project."""
    g = _get_falkordb_graph()

    # 1. Resolve workspace node
    ws_id_prefixed = f"workspace:{workspace_id}" if not workspace_id.startswith("workspace:") else workspace_id
    ws_rows = None
    for q, params in [
        ("MATCH (w:UKO) WHERE w.type = 'workspace' AND w.id = $id RETURN w.id, w.name", {"id": ws_id_prefixed}),
        ("MATCH (w:UKO) WHERE w.type = 'workspace' AND w.name = $name RETURN w.id, w.name LIMIT 1", {"name": workspace_id}),
        ("MATCH (w:UKO) WHERE w.type = 'workspace' AND w.id STARTSWITH $prefix RETURN w.id, w.name LIMIT 1", {"prefix": ws_id_prefixed}),
    ]:
        res = g.query(q, params)
        ws_rows = res.result_set if hasattr(res, "result_set") else res
        if ws_rows and ws_rows[0]:
            break

    ws_node_id = str(ws_rows[0][0]) if (ws_rows and ws_rows[0] and ws_rows[0][0]) else ""
    group_id = ws_node_id.replace("workspace:", "") if ws_node_id else workspace_id

    all_ids: set[str] = set()

    # Find by group_id
    try:
        res = g.query("MATCH (u:UKO) WHERE u.group_id = $gid RETURN u.id", {"gid": group_id})
        for tr in (res.result_set if hasattr(res, "result_set") else res):
            if tr[0]:
                all_ids.add(str(tr[0]))
    except Exception:
        pass

    # Find by part_of_workspace edges
    if ws_node_id:
        try:
            res = g.query(
                "MATCH (u:UKO)-[r:RELATES {label: 'part_of_workspace'}]->(w:UKO {id: $ws_id}) RETURN u.id",
                {"ws_id": ws_node_id},
            )
            for er in (res.result_set if hasattr(res, "result_set") else res):
                if er[0]:
                    all_ids.add(str(er[0]))
        except Exception:
            pass

    # Try prefix on group_id
    if not all_ids:
        try:
            res = g.query("MATCH (u:UKO) WHERE u.group_id STARTSWITH $prefix RETURN u.id", {"prefix": workspace_id})
            for tr in (res.result_set if hasattr(res, "result_set") else res):
                if tr[0]:
                    all_ids.add(str(tr[0]))
        except Exception:
            pass

    # Delete FalkorDB nodes
    falkordb_deleted = 0
    for uid in all_ids:
        try:
            g.query("MATCH (u:UKO {id: $id}) DETACH DELETE u", {"id": uid})
            falkordb_deleted += 1
        except Exception:
            pass
    if ws_node_id:
        try:
            g.query("MATCH (w:UKO {id: $id}) DETACH DELETE w", {"id": ws_node_id})
            falkordb_deleted += 1
        except Exception:
            pass

    await snapshot_after_graph_write(
        persisted=True,
        success_count=falkordb_deleted,
        source="project-delete",
        revision=workspace_id,
    )

    # 2. Delete from PostgreSQL
    db_deleted = False
    try:
        from ecms.persistence.database.rest_session import db_session as pg_session
        from ecms.persistence.repositories.project import ProjectRepository
        async with pg_session() as session:
            repo = ProjectRepository(session)
            db_deleted = await repo.delete(workspace_id)
    except Exception:
        pass

    # 3. Delete sessions + messages from PostgreSQL
    sessions_deleted = 0
    try:
        from ecms.persistence.database.rest_session import db_session as pg_session2
        from ecms.persistence.repositories.session import SessionRepository
        async with pg_session2() as session:
            sessions_deleted = await SessionRepository(session).delete_by_workspace(workspace_id)
    except Exception:
        pass

    # 4. Delete Mem0/Qdrant workspace collection
    mem0_deleted = False
    try:
        import qdrant_client
        ws_collection = f"ecms_mem0_{workspace_id}" if workspace_id != "default" else "ecms_mem0"
        qdrant = qdrant_client.QdrantClient(
            url=os.environ.get("ECMS_MEM0_QDRANT_URL", "http://qdrant:6333"),
        )
        try:
            qdrant.delete_collection(ws_collection)
            mem0_deleted = True
        except Exception:
            pass
    except Exception:
        pass

    # 4. Delete Redis sessions for this workspace
    redis_deleted = 0
    try:
        import redis
        r = redis.Redis.from_url(
            os.environ.get("ECMS_REDIS_URL", "redis://redis:6379/0"),
            decode_responses=True,
        )
        pattern = f"ecms:session:{workspace_id}:*"
        keys = list(r.scan_iter(match=pattern, count=100))
        if keys:
            redis_deleted = r.delete(*keys)
    except Exception:
        pass

    # 5. Delete GBrain markdown memory files on disk
    gbrain_deleted = False
    try:
        brain_dir = f"/app/memory/{workspace_id}"
        if os.path.isdir(brain_dir):
            shutil.rmtree(brain_dir)
            gbrain_deleted = True
        # Also try group_id variant
        if group_id and group_id != workspace_id:
            alt_dir = f"/app/memory/{group_id}"
            if os.path.isdir(alt_dir):
                shutil.rmtree(alt_dir)
                gbrain_deleted = True
    except Exception:
        pass

    return {
        "deleted": True,
        "workspace_id": workspace_id,
        "falkordb_nodes_removed": falkordb_deleted,
        "db_deleted": db_deleted,
        "sessions_deleted": sessions_deleted,
        "mem0_deleted": mem0_deleted,
        "redis_sessions_cleared": redis_deleted,
        "gbrain_deleted": gbrain_deleted,
    }


@router.put("/{workspace_id}")
async def edit_project(workspace_id: str, body: EditProjectRequest) -> dict:
    """Edit workspace name and connectors."""
    g = _get_falkordb_graph()
    ws_id_prefixed = f"workspace:{workspace_id}" if not workspace_id.startswith("workspace:") else workspace_id

    try:
        if body.name:
            g.query(
                "MATCH (w:UKO {id: $id}) SET w.name = $name",
                {"id": ws_id_prefixed, "name": body.name},
            )

            # Also update in PostgreSQL
            try:
                from ecms.persistence.database.rest_session import db_session as pg_session
                from ecms.persistence.repositories.project import ProjectRepository
                async with pg_session() as session:
                    repo = ProjectRepository(session)
                    await repo.upsert(
                        project_id=f"proj:{workspace_id}",
                        workspace_id=workspace_id,
                        name=body.name,
                    )
            except Exception:
                pass

            await snapshot_after_graph_write(
                persisted=True,
                success_count=1,
                source="project-update",
                revision=workspace_id,
            )

        return {"updated": True, "workspace_id": workspace_id}
    except Exception as e:
        return {"updated": False, "error": str(e)}
