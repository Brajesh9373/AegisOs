"""Authenticated delivery API for immutable knowledge-graph snapshots."""

from __future__ import annotations

import asyncio
import time
from functools import lru_cache
from typing import Annotated, Any
from uuid import uuid4

import falkordb
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy import text

from ecms.api.dependencies.providers import get_sdk
from ecms.auth import Identity
from ecms.configuration.schemas.settings import get_settings
from ecms.infrastructure.storage.factory import create_snapshot_object_store
from ecms.infrastructure.storage.object_store import ObjectStore
from ecms.persistence.database.rest_session import db_session
from ecms.persistence.models.knowledge_graph_snapshot import KnowledgeGraphSnapshot
from ecms.persistence.repositories.knowledge_graph_snapshot import (
    KnowledgeGraphSnapshotRepository,
)
from ecms.visualization.graph_changed import graph_changed
from ecms.visualization.snapshot_queue import GROUP, HEALTH_PREFIX, STREAM

router = APIRouter(prefix="/api/knowledge-graph/v2", tags=["knowledge-graph-v2"])
ARROW_CONTENT_TYPE = "application/vnd.apache.arrow.file"


def _organization_id(identity: Identity) -> str:
    """Resolve the authenticated tenant while retaining single-org compatibility."""
    return identity.tenant_id or "default"


async def require_graph_identity(request: Request) -> Identity:
    """Authenticate either the SDK JWT or the platform's active UI session."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="missing bearer token")
    try:
        return get_sdk(request).authentication.verify(token)
    except Exception:  # noqa: S110 - UI sessions use a separate token store
        pass

    async with db_session() as session:
        row = (
            await session.execute(
                text(
                    "SELECT users.id, users.email, users.role "
                    "FROM auth_sessions JOIN users ON users.id = auth_sessions.userid "
                    "WHERE auth_sessions.token = :token "
                    "AND CAST(auth_sessions.expiresat AS BIGINT) > :now"
                ),
                {
                    "token": token,
                    "now": int(time.time() * 1000),
                },
            )
        ).first()
    if row is None:
        raise HTTPException(status_code=401, detail="invalid or expired session")
    return Identity(subject=row.email, roles=[row.role or "user"])


def _is_admin(identity: Identity) -> bool:
    roles = {role.lower() for role in identity.roles}
    return bool({"admin", "administrator", "superadmin", "super admin"} & roles)


class ClientMetric(BaseModel):
    """Bounded browser renderer telemetry payload."""

    renderer: str = Field(pattern="^(cosmos|d3)$")
    event: str = Field(pattern="^(ready|load_failed|webgl_fallback|unmounted)$")
    duration_ms: int | None = Field(default=None, ge=0, le=600_000)


@lru_cache(maxsize=1)
def _object_store() -> ObjectStore:
    return create_snapshot_object_store(get_settings())


def _snapshot_manifest(
    current: KnowledgeGraphSnapshot | None,
    latest: KnowledgeGraphSnapshot | None,
) -> dict[str, Any]:
    build_state = latest.state if latest is not None else "missing"
    result: dict[str, Any] = {
        "state": build_state,
        "stale": bool(current and latest and latest.id != current.id),
        "error": latest.error_summary if latest and latest.state == "failed" else None,
        "snapshot": None,
    }
    if current is None:
        return result
    settings = get_settings()
    supported = (
        current.point_count <= settings.knowledge_graph_max_client_nodes
        and current.link_count <= settings.knowledge_graph_max_client_links
    )
    store = _object_store()
    points_url = store.presign_get(current.points_object_key) if current.points_object_key else None
    links_url = store.presign_get(current.links_object_key) if current.links_object_key else None
    result["snapshot"] = {
        "version": current.version,
        "schema_version": current.schema_version,
        "point_count": current.point_count,
        "link_count": current.link_count,
        "points_bytes": current.points_bytes,
        "links_bytes": current.links_bytes,
        "points_checksum": current.points_checksum,
        "links_checksum": current.links_checksum,
        "points_url": points_url or f"/api/knowledge-graph/v2/snapshots/{current.version}/points",
        "links_url": links_url or f"/api/knowledge-graph/v2/snapshots/{current.version}/links",
        "generated_at": current.completed_at.isoformat() if current.completed_at else None,
        "source_watermark": current.source_watermark,
        "capacity": {
            "supported": supported,
            "max_nodes": settings.knowledge_graph_max_client_nodes,
            "max_links": settings.knowledge_graph_max_client_links,
        },
    }
    return result


@router.get("/manifest")
async def get_manifest(
    request: Request,
    identity: Annotated[Identity, Depends(require_graph_identity)],
    if_none_match: Annotated[str | None, Header()] = None,
) -> Response:
    """Return current immutable snapshot details plus transient build state."""
    started_at = time.perf_counter()
    organization_id = _organization_id(identity)
    async with db_session() as session:
        repository = KnowledgeGraphSnapshotRepository(session)
        current = await repository.get_current(organization_id)
        latest = await repository.get_latest(organization_id)
    etag = f'"{current.version}"' if current else None
    try:
        if etag and if_none_match == etag and latest and latest.id == current.id:
            return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag})
        import json

        body = json.dumps(_snapshot_manifest(current, latest))
        headers = {"Cache-Control": "no-store"}
        if etag:
            headers["ETag"] = etag
        return Response(content=body, media_type="application/json", headers=headers)
    finally:
        request.app.state.knowledge_graph_delivery_metrics["manifest_latency"].observe(
            time.perf_counter() - started_at
        )


@router.get("/config")
async def get_renderer_config(
    identity: Annotated[Identity, Depends(require_graph_identity)],
) -> dict[str, str]:
    """Return the runtime renderer selection to an authenticated client."""
    _organization_id(identity)
    settings = get_settings()
    allowed_roles = settings.cosmos_roles
    identity_roles = {role.lower() for role in identity.roles}
    enabled = settings.knowledge_graph_renderer == "cosmos" and (
        "*" in allowed_roles or bool(allowed_roles & identity_roles)
    )
    return {"renderer": "cosmos" if enabled else "d3"}


@router.get("/status")
async def get_snapshot_status(
    identity: Annotated[Identity, Depends(require_graph_identity)],
) -> dict[str, Any]:
    """Return administrator diagnostics for queue, worker, and current snapshot health."""
    if not _is_admin(identity):
        raise HTTPException(status_code=403, detail="administrator role required")
    organization_id = _organization_id(identity)
    async with db_session() as session:
        repository = KnowledgeGraphSnapshotRepository(session)
        current = await repository.get_current(organization_id)
        latest = await repository.get_latest(organization_id)

    redis = Redis.from_url(get_settings().redis_url)
    try:
        queue_depth = await redis.xlen(STREAM)
        try:
            pending = await redis.xpending(STREAM, GROUP)
            pending_count = int(pending.get("pending", 0))
        except Exception:
            pending_count = 0
        workers: list[str] = []
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=f"{HEALTH_PREFIX}*", count=100)
            workers.extend(key.decode() if isinstance(key, bytes) else str(key) for key in keys)
            if cursor == 0:
                break
    finally:
        await redis.aclose()

    artifact_health = "missing"
    if current and current.points_object_key and current.links_object_key:
        store = _object_store()
        try:
            points, links = await asyncio.gather(
                store.stat_object(current.points_object_key),
                store.stat_object(current.links_object_key),
            )
            artifact_health = (
                "healthy"
                if points.size == current.points_bytes and links.size == current.links_bytes
                else "corrupt"
            )
        except Exception:
            artifact_health = "unavailable"
    return {
        "healthy": bool(current and artifact_health == "healthy" and workers),
        "queue": {"entries": queue_depth, "pending": pending_count},
        "workers": {"active": len(workers)},
        "snapshot": {
            "current_version": current.version if current else None,
            "latest_state": latest.state if latest else "missing",
            "point_count": current.point_count if current else 0,
            "link_count": current.link_count if current else 0,
            "artifacts": artifact_health,
            "completed_at": current.completed_at.isoformat()
            if current and current.completed_at
            else None,
        },
    }


def _parse_range(value: str | None, size: int) -> tuple[int, int] | None:
    if value is None:
        return None
    if not value.startswith("bytes=") or "," in value:
        raise HTTPException(status_code=416, detail="unsupported byte range")
    start_text, separator, end_text = value[6:].partition("-")
    if not separator or not start_text:
        raise HTTPException(status_code=416, detail="unsupported byte range")
    try:
        start = int(start_text)
        end = int(end_text) if end_text else size - 1
    except ValueError as exc:
        raise HTTPException(status_code=416, detail="invalid byte range") from exc
    if start < 0 or start >= size or end < start:
        raise HTTPException(status_code=416, detail="byte range out of bounds")
    return start, min(end, size - 1)


@router.get("/snapshots/{version}/{artifact}")
async def stream_snapshot(
    request: Request,
    version: str,
    artifact: str,
    identity: Annotated[Identity, Depends(require_graph_identity)],
    range_header: Annotated[str | None, Header(alias="Range")] = None,
) -> StreamingResponse:
    """Stream one immutable Arrow artifact with bounded server memory."""
    if artifact not in {"points", "links"}:
        raise HTTPException(status_code=404, detail="snapshot artifact not found")
    async with db_session() as session:
        snapshot = await KnowledgeGraphSnapshotRepository(session).get_version(
            _organization_id(identity),
            version,
        )
    if snapshot is None:
        raise HTTPException(status_code=404, detail="snapshot version not found")
    key = snapshot.points_object_key if artifact == "points" else snapshot.links_object_key
    checksum = snapshot.points_checksum if artifact == "points" else snapshot.links_checksum
    expected_size = snapshot.points_bytes if artifact == "points" else snapshot.links_bytes
    if key is None or checksum is None:
        raise HTTPException(status_code=503, detail="snapshot artifact is incomplete")

    store = _object_store()
    now = time.monotonic()
    stat_cache: dict[str, tuple[float, Any]] = getattr(
        request.app.state,
        "knowledge_graph_stat_cache",
        {},
    )
    request.app.state.knowledge_graph_stat_cache = stat_cache
    stat_locks: dict[str, asyncio.Lock] = getattr(
        request.app.state,
        "knowledge_graph_stat_locks",
        {},
    )
    request.app.state.knowledge_graph_stat_locks = stat_locks
    try:
        cached = stat_cache.get(key)
        if cached and cached[0] > now:
            info = cached[1]
        else:
            lock = stat_locks.setdefault(key, asyncio.Lock())
            async with lock:
                cached = stat_cache.get(key)
                if cached and cached[0] > time.monotonic():
                    info = cached[1]
                else:
                    info = await store.stat_object(key)
                    stat_cache[key] = (time.monotonic() + 30, info)
    except Exception as exc:
        request.app.state.knowledge_graph_delivery_metrics["download_failures"].labels(
            artifact=artifact, reason="storage_unavailable"
        ).inc()
        raise HTTPException(
            status_code=503,
            detail="snapshot storage is temporarily unavailable",
        ) from exc
    if info.size != expected_size:
        request.app.state.knowledge_graph_delivery_metrics["download_failures"].labels(
            artifact=artifact, reason="size_mismatch"
        ).inc()
        raise HTTPException(status_code=503, detail="snapshot artifact size mismatch")
    requested = _parse_range(range_header, info.size)
    start, end = requested or (0, info.size - 1)
    headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "public, max-age=31536000, immutable",
        "ETag": f'"{checksum}"',
        "Content-Length": str(end - start + 1),
    }
    response_status = status.HTTP_200_OK
    if requested:
        response_status = status.HTTP_206_PARTIAL_CONTENT
        headers["Content-Range"] = f"bytes {start}-{end}/{info.size}"

    async def monitored_stream():
        try:
            async for chunk in store.iter_object(key, start=start, end=end):
                yield chunk
        except Exception:
            request.app.state.knowledge_graph_delivery_metrics["download_failures"].labels(
                artifact=artifact, reason="stream_interrupted"
            ).inc()
            raise

    return StreamingResponse(
        monitored_stream(),
        status_code=response_status,
        media_type=ARROW_CONTENT_TYPE,
        headers=headers,
    )


@router.post("/client-metrics", status_code=status.HTTP_204_NO_CONTENT)
async def record_client_metric(
    body: ClientMetric,
    request: Request,
    identity: Annotated[Identity, Depends(require_graph_identity)],
) -> Response:
    """Record allow-listed, low-cardinality browser renderer outcomes."""
    _organization_id(identity)
    collectors = request.app.state.knowledge_graph_delivery_metrics
    collectors["client_events"].labels(
        renderer=body.renderer,
        event=body.event,
    ).inc()
    if body.duration_ms is not None:
        collectors["client_load_duration"].labels(
            renderer=body.renderer,
        ).observe(body.duration_ms / 1_000)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _load_node_metadata(node_id: str) -> dict[str, Any] | None:
    settings = get_settings()
    graph = falkordb.FalkorDB.from_url(settings.falkordb_url).select_graph(settings.falkordb_graph)
    result = graph.query(
        """
        MATCH (node {id: $node_id})
        OPTIONAL MATCH (node)-[relationship]-(neighbor)
        RETURN properties(node), type(relationship), properties(neighbor)
        LIMIT 101
        """,
        {"node_id": node_id},
    )
    rows = result.result_set
    if not rows:
        return None
    properties = rows[0][0]
    connections = [
        {"relationship": row[1], "node": row[2]}
        for row in rows
        if row[1] is not None and row[2] is not None
    ]
    return {"node": properties, "connections": connections[:100]}


@router.get("/nodes/{node_id}")
async def get_node_metadata(
    node_id: str,
    identity: Annotated[Identity, Depends(require_graph_identity)],
) -> dict[str, Any]:
    """Fetch full inspector data only after a user selects a node."""
    _organization_id(identity)
    result = await asyncio.to_thread(_load_node_metadata, node_id)
    if result is None:
        raise HTTPException(status_code=404, detail="knowledge node not found")
    return result


@router.post("/rebuild", status_code=status.HTTP_202_ACCEPTED)
async def rebuild_snapshot(
    identity: Annotated[Identity, Depends(require_graph_identity)],
    request: Request,
) -> dict[str, Any]:
    """Queue an audited administrator rebuild request."""
    if not _is_admin(identity):
        raise HTTPException(status_code=403, detail="administrator role required")
    async with db_session() as session:
        user_id = (
            await session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": identity.subject},
            )
        ).scalar_one_or_none()
        if user_id is not None:
            await session.execute(
                text(
                    "INSERT INTO audit_logs "
                    "(id, action, userid, details, timestamp) "
                    "VALUES (:id, :action, :user_id, :details, NOW())"
                ),
                {
                    "id": str(uuid4()),
                    "action": "Knowledge Graph Snapshot Rebuild",
                    "user_id": user_id,
                    "details": f"Organization {_organization_id(identity)}",
                },
            )
    accepted = await graph_changed(
        _organization_id(identity),
        source="admin",
        revision=request.headers.get("X-Request-ID"),
    )
    return {"accepted": accepted, "state": "queued" if accepted else "coalesced"}
