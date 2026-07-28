from fastapi import APIRouter
from pydantic import BaseModel

from legacy_ecms import __version__
from legacy_ecms.api.graph_context import create_graph_client

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class GraphHealthResponse(BaseModel):
    status: str
    graph: str
    error: str | None = None


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="ecms", version=__version__)


@router.get("/health/graph", response_model=GraphHealthResponse)
async def graph_health() -> GraphHealthResponse:
    graph = create_graph_client()
    try:
        await graph.initialize()
        return GraphHealthResponse(status="ok", graph="graphiti-falkordb")
    except Exception as exc:
        return GraphHealthResponse(status="error", graph="graphiti-falkordb", error=str(exc))
    finally:
        await graph.close()
