from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from legacy_ecms.api.middleware.auth import ApiKeyMiddleware
from legacy_ecms.api.middleware.metrics import MetricsMiddleware
from legacy_ecms.api.routes.graph import router as graph_router
from legacy_ecms.api.routes.health import router as health_router
from legacy_ecms.api.routes.ingest import router as ingest_router
from legacy_ecms.api.routes.memory import router as memory_router
from legacy_ecms.api.routes.metrics import router as metrics_router
from legacy_ecms.api.routes.providers import router as providers_router
from legacy_ecms.api.routes.query import router as query_router
from legacy_ecms.api.routes.workspaces import router as workspaces_router
from legacy_ecms.config import get_settings

UI_DIR = Path(__file__).resolve().parent / "ui"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Enterprise Cognitive Memory System",
        version="0.1.0",
        description="Vendor-agnostic cognitive memory API for enterprise knowledge graphs.",
        root_path_in_servers=False,
    )
    settings = get_settings()
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(ApiKeyMiddleware, settings=settings)
    app.include_router(health_router)
    app.include_router(graph_router)
    app.include_router(providers_router)
    app.include_router(ingest_router)
    app.include_router(memory_router)
    app.include_router(query_router)
    app.include_router(workspaces_router)
    app.include_router(metrics_router)

    if UI_DIR.exists():
        @app.get("/")
        async def console() -> FileResponse:
            return FileResponse(UI_DIR / "index.html")

        app.mount("/assets", StaticFiles(directory=UI_DIR / "assets"), name="assets")

    return app


app = create_app()
