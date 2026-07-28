import asyncio

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(tags=["legacy-graph"])


class GraphNode(BaseModel):
    id: str
    label: str
    group: str
    title: str | None = None
    source_id: str | None = None
    source_url: str | None = None
    source_group: str | None = None
    extraction_method: str | None = None
    node_confidence: float | None = None
    domain: str | None = None


class GraphEdge(BaseModel):
    id: str
    from_: str
    to: str
    label: str
    title: str | None = None
    confidence: float | None = None
    extraction_method: str | None = None
    pipeline_stage: str | None = None
    evidence_snippet: str | None = None


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    node_count: int
    edge_count: int


def _to_str(val, default=""):
    return str(val) if val is not None else default


def _source_group(source: str, source_id: str) -> str | None:
    if not source_id:
        return None
    base = source_id.split("#", 1)[0]
    known_sources = ("git", "mysql", "jira", "slack", "confluence", "manual", "semantic", "temporal")
    if ":" in base:
        prefix, remainder = base.split(":", 1)
        if prefix in known_sources and remainder:
            if prefix in {"semantic", "temporal"} and ":" in remainder:
                return remainder
            return base
    return f"{source}:{base}" if source else base


def load_graph_data_sync(q: str | None = None) -> GraphResponse:
    """Load the complete graph synchronously for worker and compatibility use."""
    import falkordb
    from legacy_ecms.config import get_settings
    settings = get_settings()
    db = falkordb.FalkorDB(
        host=settings.falkordb_host, port=settings.falkordb_port,
        password=settings.falkordb_password or None)
    g = db.select_graph(settings.falkordb_database)

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    seen: set[str] = set()
    seen_edges: set[str] = set()
    needed: set[str] = set()
    ctr = 0

    def _row(r):
        return r.result_set if hasattr(r, "result_set") else r

    def _append_uko_node(row) -> None:
        uid = _to_str(row[0])
        if not uid or uid in seen:
            return
        seen.add(uid)
        name = _to_str(row[1])
        src = _to_str(row[2])
        utype = _to_str(row[3]) if len(row) > 3 else ""
        source = _to_str(row[5]) if len(row) > 5 else ""
        source_id = _to_str(row[6]) if len(row) > 6 else ""
        nconf_val = row[8] if len(row) > 8 else None
        nconf = None
        if nconf_val is not None:
            try:
                nconf = float(str(nconf_val))
            except (ValueError, TypeError):
                nconf = None
        grp = utype or "episode"
        if "file" in grp.lower():
            grp = "file"
        domain_val = _to_str(row[9]) if len(row) > 9 else ""
        source_url = _to_str(row[10]) if len(row) > 10 else ""
        nodes.append(
            GraphNode(
                id=uid,
                label=(name or uid)[:60],
                group=grp,
                title=src[:100],
                source_id=source_id or None,
                source_url=source_url or None,
                source_group=_source_group(source, source_id),
                extraction_method=None,
                node_confidence=nconf,
                domain=domain_val or None,
            )
        )

    # 1. Fetch ALL edges — paginated to bypass FalkorDB's internal 10000-row cursor limit
    edge_queries = [
        ("MATCH (u:UKO)-[r:RELATES]->(t:UKO) "
         "WHERE $q IS NULL OR toLower(u.name) CONTAINS toLower($q) OR toLower(t.name) CONTAINS toLower($q) "
         "OR toLower(u.source_id) CONTAINS toLower($q) OR toLower(t.source_id) CONTAINS toLower($q) "
         "RETURN u.id, r.label, t.id ORDER BY u.id SKIP {skip} LIMIT 5000",
         {"q": q}),
        ("MATCH (e:Episode)-[r:RELATES]->(t:Episode) RETURN e.uuid, r.label, t.uuid ORDER BY e.uuid SKIP {skip} LIMIT 5000",
         {}),
        ("MATCH (a)-[r:RELATES_TO|MENTIONS]->(b) RETURN a.uuid, type(r) as rtype, b.uuid ORDER BY a.uuid SKIP {skip} LIMIT 5000",
         {}),
    ]

    for base_cypher, params in edge_queries:
        skip = 0
        while True:
            cypher = base_cypher.replace("{skip}", str(skip))
            try:
                result = g.query(cypher, params)
                rows = _row(result)
            except Exception:
                break
            if not rows:
                break
            for row in rows:
                if len(row) < 3:
                    continue
                src, lbl, tgt = _to_str(row[0]), _to_str(row[1], "related"), _to_str(row[2])
                if not src or not tgt:
                    continue
                ek = f"{src}--{lbl}-->{tgt}"
                if ek in seen_edges:
                    continue
                seen_edges.add(ek)
                edges.append(GraphEdge(
                    id=f"e-{ctr}", from_=src, to=tgt, label=lbl,
                ))
                ctr += 1
                needed.add(src)
                needed.add(tgt)
            skip += 5000

    # 2. Fetch ALL UKO nodes referenced by edges
    if needed:
        batch = [uid for uid in needed if uid]
        for i in range(0, len(batch), 200):
            chunk = [uid for uid in batch[i:i+200] if "'" not in uid]
            if not chunk:
                continue
            ids = ", ".join(f"'{uid}'" for uid in chunk)
            try:
                for row in _row(g.query(
                    f"MATCH (u:UKO) WHERE u.id IN [{ids}] "
                    "RETURN u.id, u.name, u.source_description, u.type, u.layer, u.source, u.source_id, u.extraction_method, u.node_confidence, u.domain, u.source_url"
                )):
                    _append_uko_node(row)
            except Exception:
                pass

    # 3. Fetch standalone UKO nodes too. A provider can legitimately write
    # nodes before it has valid relationships, and the UI should still display
    # the imported knowledge graph instead of an empty state.
    skip = 0
    while True:
        cypher = (
            "MATCH (u:UKO) "
            "WHERE $q IS NULL OR toLower(u.id) CONTAINS toLower($q) "
            "OR toLower(u.name) CONTAINS toLower($q) "
            "OR toLower(u.source_id) CONTAINS toLower($q) "
            "OR toLower(u.source_description) CONTAINS toLower($q) "
            "RETURN u.id, u.name, u.source_description, u.type, u.layer, u.source, u.source_id, u.extraction_method, u.node_confidence, u.domain, u.source_url "
            f"ORDER BY u.id SKIP {skip} LIMIT 5000"
        )
        try:
            rows = _row(g.query(cypher, {"q": q}))
        except Exception:
            break
        if not rows:
            break
        for row in rows:
            _append_uko_node(row)
        skip += 5000

    return GraphResponse(nodes=nodes, edges=edges, node_count=len(nodes), edge_count=len(edges))


@router.get("/data", response_model=GraphResponse)
async def get_graph_data(
    q: str | None = Query(default=None),
) -> GraphResponse:
    """Load the legacy graph without blocking the FastAPI event loop."""
    return await asyncio.to_thread(load_graph_data_sync, q)


@router.get("/consistency")
async def get_graph_consistency() -> dict:
    import falkordb
    from ecms.config import get_settings
    from legacy_ecms.core.consistency import ConsistencyChecker

    settings = get_settings()
    db = falkordb.FalkorDB(
        host=settings.falkordb_host, port=settings.falkordb_port,
        password=settings.falkordb_password or None)
    g = db.select_graph(settings.falkordb_database)
    checker = ConsistencyChecker(g)
    report = await checker.check_all()
    return {
        "total_nodes": report.total_nodes,
        "orphan_count": report.orphan_count,
        "broken_containment_count": report.broken_containment_count,
        "unsupported_concept_count": report.unsupported_concept_count,
        "phantom_target_count": report.phantom_target_count,
        "type_mismatch_count": report.type_mismatch_count,
    }


@router.post("/consistency/repair")
async def repair_graph_consistency() -> dict:
    import falkordb
    from ecms.config import get_settings
    from legacy_ecms.core.consistency import ConsistencyChecker

    settings = get_settings()
    db = falkordb.FalkorDB(
        host=settings.falkordb_host, port=settings.falkordb_port,
        password=settings.falkordb_password or None)
    g = db.select_graph(settings.falkordb_database)
    checker = ConsistencyChecker(g)
    return await checker.repair()
