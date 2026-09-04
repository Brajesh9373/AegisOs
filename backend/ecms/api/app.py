"""FastAPI application factory (SECTION 69/105)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from ecms import __version__
from ecms.api.errors.handlers import register_exception_handlers
from ecms.api.graphql.router import create_graphql_router
from ecms.api.middleware.context import RequestContextMiddleware
from ecms.api.middleware.observability import MetricsMiddleware, TracingMiddleware
from ecms.api.middleware.rate_limit import RateLimitMiddleware
from ecms.api.rest import auth, cognition, health, metrics, system, projects, session_chat, agents, policies, categories, categorize, agent_profiles
from ecms.api.rest.platform import router as platform_router
from ecms.api.rest.discovery import router as discovery_router
from ecms.api.rest.meetings import router as meetings_router
from ecms.api.rest.organization import router as organization_router
from ecms.api.rest.organization import tool_router as org_tool_router
from ecms.api.rest.governance import router as governance_router
from ecms.api.rest.knowledge_graph_snapshots import router as knowledge_graph_snapshot_router
from ecms.api.rest.connector_ingestions import router as connector_ingestion_router
from ecms.api.websocket.endpoints import router as websocket_router
from ecms.api.websocket.manager import ConnectionManager
from ecms.api.websocket.terminal import router as terminal_router
from ecms.knowledge.services.watcher import KnowledgeWatcher
from ecms.sdk import EcmsSDK, create_sdk
from ecms.sdk.cognitive import create_cognitive_system
from ecms.websocket import TelemetryBridge

# Legacy provider integration — live Git/MySQL sync, generic UKO ingestion,
# workspace management, GBrain memory, mem0 semantic memory, and cognitive agent.
from legacy_ecms.api.routes.providers import router as legacy_providers_router
from legacy_ecms.api.routes.workspaces import router as legacy_workspaces_router
from legacy_ecms.api.routes.memory import router as legacy_memory_router
from legacy_ecms.api.routes.ingest import router as legacy_ingest_router
from legacy_ecms.api.routes.graph import router as legacy_graph_router
from legacy_ecms.api.routes.query import router as legacy_query_router

__all__ = ["create_app"]

_API_V1 = "/api/v1"


def create_app(sdk: EcmsSDK | None = None) -> FastAPI:
    resolved = sdk or create_sdk()
    app = FastAPI(
        title="Enterprise Cognitive Memory System",
        version=__version__,
        description="ECMS foundation REST API gateway.",
        openapi_url=f"{_API_V1}/openapi.json",
        docs_url=f"{_API_V1}/docs",
        redoc_url=f"{_API_V1}/redoc",
    )
    app.state.sdk = resolved
    app.state.cognitive = create_cognitive_system(
        event_bus=resolved.events,
        falkordb_url=resolved.settings.falkordb_url,
        falkordb_graph=resolved.settings.falkordb_graph,
    )

    ws_manager = ConnectionManager()
    telemetry = TelemetryBridge(ws_manager)
    telemetry.register(resolved.events)
    app.state.ws_manager = ws_manager
    app.state.ws_telemetry = telemetry
    app.state.knowledge_graph_delivery_metrics = {
        "manifest_latency": resolved.metrics.histogram(
            "knowledge_graph_manifest_duration_seconds",
            "Authenticated snapshot manifest response latency.",
        ),
        "download_failures": resolved.metrics.counter(
            "knowledge_graph_snapshot_download_failures",
            "Snapshot artifact download failures.",
            ("artifact", "reason"),
        ),
        "client_events": resolved.metrics.counter(
            "knowledge_graph_client_events",
            "Knowledge Graph renderer outcomes reported by browsers.",
            ("renderer", "event"),
        ),
        "client_load_duration": resolved.metrics.histogram(
            "knowledge_graph_client_load_duration_seconds",
            "Browser time from Knowledge Graph load start to renderer readiness.",
            ("renderer",),
        ),
    }

    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(RateLimitMiddleware, limit=resolved.settings.rate_limit_per_minute, window_seconds=60.0)
    app.add_middleware(MetricsMiddleware, metrics=resolved.metrics)
    app.add_middleware(TracingMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(CORSMiddleware, allow_origins=resolved.settings.cors_origins, allow_credentials=resolved.settings.cors_allow_credentials, allow_methods=resolved.settings.cors_methods, allow_headers=resolved.settings.cors_headers)

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(metrics.router)
    app.include_router(system.router)
    app.include_router(health.router, prefix=_API_V1)
    app.include_router(system.router, prefix=_API_V1)
    app.include_router(cognition.router, prefix=_API_V1)
    app.include_router(session_chat.router, prefix=_API_V1)
    app.include_router(projects.router)
    app.include_router(auth.router)
    app.include_router(agents.router)
    app.include_router(agent_profiles.router)
    app.include_router(policies.router)
    app.include_router(categories.router)
    app.include_router(categorize.router)
    app.include_router(platform_router)
    app.include_router(discovery_router)
    app.include_router(meetings_router)
    app.include_router(organization_router)
    app.include_router(org_tool_router)
    app.include_router(governance_router)
    app.include_router(knowledge_graph_snapshot_router)
    app.include_router(connector_ingestion_router)
    app.include_router(create_graphql_router(), prefix="/graphql")
    app.include_router(websocket_router)
    app.include_router(terminal_router)

    # ── Legacy live provider routes (Git and MySQL) ──
    app.include_router(legacy_providers_router)
    app.include_router(legacy_workspaces_router)
    app.include_router(legacy_memory_router)
    app.include_router(legacy_ingest_router)
    app.include_router(legacy_graph_router, prefix="/legacy-graph")
    app.include_router(legacy_query_router)

    @app.on_event("startup")
    async def _start_watcher() -> None:
        cognitive = app.state.cognitive
        watcher = KnowledgeWatcher.get_or_create(
            cognitive.knowledge,
            cognitive.graph,
            "/workspace",
            organization_id="default"
        )  # type: ignore[no-untyped-call]
        loop = asyncio.get_event_loop()
        loop.create_task(watcher.watch_forever(interval=3.0))
        app.state.watcher = watcher

        # Memory bridge: continuous sync every 2 minutes (lightweight — 5 nodes max)
        import asyncio as _asyncio
        loop.create_task(_run_bridge_worker())
        loop.create_task(_reset_stuck_team_statuses())

    return app


async def _run_bridge_worker() -> None:
    """Continuous bridge sync — lightweight, handles knowledge-layer promotion."""
    import asyncio as _asyncio, logging
    logger = logging.getLogger("ecms.bridge")
    await _asyncio.sleep(30)  # initial delay for FalkorDB readiness

    from ecms.api.rest.session_chat import sync_all_memory
    while True:
        try:
            result = await sync_all_memory()
            if result.get("synced", 0):
                logger.info("Bridge synced %d new atoms (total: %d)", result["synced"], result["total"])
        except Exception as e:
            logger.warning("Bridge sync failed: %s", e)
        await _asyncio.sleep(120)  # every 2 minutes


async def _reset_stuck_team_statuses() -> None:
    """Reset team_status='generating' to 'failed' on startup so the workspace
    can offer a Regenerate button instead of being stuck forever.

    This is the safety net for background `_run_team_design` tasks that died
    with the container — the only state they leave behind is `generating`.
    """
    import asyncio as _asyncio, logging
    logger = logging.getLogger("ecms.startup")
    await _asyncio.sleep(5)  # let migrations finish
    try:
        from ecms.persistence.database.rest_session import db_session
        from sqlalchemy import text
        async with db_session() as session:
            result = await session.execute(text(
                "UPDATE business_projects SET team_status='failed', updatedat=NOW() "
                "WHERE team_status = 'generating'"
            ))
            count = result.rowcount or 0
            if count:
                logger.warning(
                    "[startup] reset %d stuck 'generating' projects to 'failed' "
                    "(background team_design tasks were lost to container restart)",
                    count,
                )
            else:
                logger.info("[startup] no stuck 'generating' projects found")
    except Exception as exc:
        logger.warning("[startup] could not reset stuck team statuses: %s", exc)
