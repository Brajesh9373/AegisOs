"""System health and readiness routes (SECTION 16/102)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from ecms import __version__
from ecms.api.dependencies.providers import get_sdk
from ecms.sdk import EcmsSDK

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "service": "ecms", "version": __version__}


@router.get("/ready")
async def ready(sdk: EcmsSDK = Depends(get_sdk)) -> dict[str, Any]:
    """Readiness probe reporting subsystem health."""
    subsystem_health = await sdk.health()
    return {"status": "ready", **subsystem_health}


@router.get("/health/graph")
async def health_graph(request: Request) -> dict[str, Any]:
    """Graph subsystem health — verifies connectivity and reports store type."""
    graph = request.app.state.cognitive.graph
    try:
        stats = await graph.statistics()
        return {
            "status": "healthy",
            "store": type(graph._store).__name__,
            **stats,
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "store": type(graph._store).__name__ if graph._store else "none",
            "error": str(exc),
        }
