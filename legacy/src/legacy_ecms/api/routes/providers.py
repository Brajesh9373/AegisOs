import json
import subprocess

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, SecretStr

from legacy_ecms.api.graph_context import orchestrator_context
from legacy_ecms.config import get_settings
from legacy_ecms.pipeline.workspace import attach_ukos_to_workspace
from legacy_ecms.providers.git import GitProvider
from legacy_ecms.providers.mysql import MySQLProvider

import asyncio
from ecms.agent.categorize import run_categorization
from ecms.visualization.graph_changed import snapshot_after_graph_write

router = APIRouter(prefix="/providers", tags=["providers"])


async def _trigger_categorization(workspace_id: str, project_id: str) -> None:
    """Fire-and-forget categorization after sync."""
    try:
        import asyncio
        from ecms.agent.categorize import run_categorization

        asyncio.create_task(run_categorization(workspace_id, project_id))
    except Exception as exc:  # noqa: BLE001
        import logging
        logging.getLogger("ecms.providers").warning("categorization trigger failed: %s", exc)


async def _db_upsert_connector(workspace_id: str, workspace_name: str, connector_type: str, config: dict) -> None:
    """Upsert project + connector in PostgreSQL."""
    try:
        from ecms.persistence.database.rest_session import db_session as pg_session
        from ecms.persistence.repositories.project import ProjectRepository
        async with pg_session() as s:
            repo = ProjectRepository(s)
            await repo.upsert(
                project_id=f"proj:{workspace_id}",
                workspace_id=workspace_id,
                name=workspace_name,
                connectors=[{"type": connector_type, "config": config}],
            )
    except Exception:
        pass


def _persist_connector(workspace_id: str | None, connector: dict) -> None:
    """Merge a connector config into the workspace node's `connectors` JSON property.

    Stores only non-secret fields so the edit form can pre-fill them.
    Secrets (token/password) are intentionally omitted.
    """
    if not workspace_id:
        return
    try:
        import falkordb
        from legacy_ecms.config import get_settings as _get

        s = _get()
        db = falkordb.FalkorDB(host=s.falkordb_host, port=s.falkordb_port, password=s.falkordb_password or None)
        g = db.select_graph(s.falkordb_database)
        ws_id = f"workspace:{workspace_id}" if not workspace_id.startswith("workspace:") else workspace_id

        existing = []
        try:
            res = g.query("MATCH (w:UKO {id: $id}) RETURN w.connectors", {"id": ws_id})
            rs = res.result_set if hasattr(res, "result_set") else res
            if rs and rs[0] and rs[0][0]:
                raw = rs[0][0]
                existing = json.loads(raw) if isinstance(raw, str) else (raw or [])
        except Exception:
            existing = []

        # Replace any existing entry of the same type+key, else append
        ctype = connector.get("type")
        match_key = connector.get("key")
        filtered = [
            c for c in existing
            if not (c.get("type") == ctype and (c.get("key") == match_key or (match_key is None)))
        ]
        filtered.append(connector)
        g.query(
            "MATCH (w:UKO {id: $id}) SET w.connectors = $val",
            {"id": ws_id, "val": json.dumps(filtered)},
        )
    except Exception:
        pass


class ProviderInfo(BaseModel):
    name: str
    version: str
    capabilities: list[str]


class GitSyncRequest(BaseModel):
    repo_url: str = Field(min_length=1)
    access_token: SecretStr | None = None
    platform: str | None = Field(default=None, pattern="^(github|bitbucket)$")
    branch: str | None = None
    username: str | None = None
    persist: bool = False
    workspace_id: str | None = None
    workspace_name: str | None = None


class GitSyncResponse(BaseModel):
    provider: str
    platform: str
    repo_url: str
    resource_id: str
    uko_count: int
    episode_count: int
    persisted: bool
    write_success_count: int = 0
    write_failure_count: int = 0
    write_errors: list[str] = Field(default_factory=list)


class MySQLSyncRequest(BaseModel):
    host: str = Field(min_length=1)
    port: int = 3306
    user: str = Field(min_length=1)
    password: SecretStr
    database: str = Field(min_length=1)
    connect_timeout: int = 10
    persist: bool = False
    workspace_id: str | None = None
    workspace_name: str | None = None


class MySQLSyncResponse(BaseModel):
    provider: str
    database: str
    uko_count: int
    episode_count: int
    persisted: bool
    write_success_count: int = 0
    write_failure_count: int = 0
    write_errors: list[str] = Field(default_factory=list)


@router.get("", response_model=list[ProviderInfo])
async def list_providers() -> list[ProviderInfo]:
    return [
        ProviderInfo(
            name="git",
            version="0.2.0",
            capabilities=[
                "discover",
                "sync",
                "files",
                "commits",
                "github-url",
                "bitbucket-url",
                "python-structure",
            ],
        ),
        ProviderInfo(
            name="jira",
            version="0.1.0",
            capabilities=["discover", "sync", "tickets", "comments", "status-events"],
        ),
        ProviderInfo(
            name="mysql",
            version="0.2.0",
            capabilities=["discover", "sync", "live-connection", "schemas", "tables", "columns", "foreign-keys"],
        ),
    ]


@router.post("/git/sync", response_model=GitSyncResponse)
async def sync_git_repository(request: GitSyncRequest, background_tasks: BackgroundTasks) -> GitSyncResponse:
    raise HTTPException(
        status_code=410,
        detail={
            "code": "SYNCHRONOUS_GIT_INGESTION_RETIRED",
            "message": (
                "Git ingestion is asynchronous. Create a source-control connection, "
                "then submit POST /api/connector-ingestions."
            ),
        },
    )

    # Kept temporarily as migration reference; this code is unreachable and
    # must be deleted after all external clients adopt the asynchronous API.
    settings = get_settings()
    provider = GitProvider(clone_root=settings.git_default_clone_path)
    try:
        await provider.authenticate(
            {
                "repo_url": request.repo_url,
                "access_token": request.access_token.get_secret_value() if request.access_token else "",
                "platform": request.platform,
                "branch": request.branch,
                "username": request.username,
                "clone_root": settings.git_default_clone_path,
            }
        )
        resource_id = (await provider.discover())[0]
        ukos = [uko async for uko in provider.sync(resource_id)]
        if request.workspace_id:
            ukos = attach_ukos_to_workspace(ukos, request.workspace_id, request.workspace_name)
    except (RuntimeError, ValueError, IndexError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail=f"Git operation timed out: {exc}") from exc

    if request.workspace_id:
        remote = provider.remote_for(resource_id)
        _persist_connector(
            request.workspace_id,
            {
                "type": "git",
                "key": request.repo_url,
                "repo_url": request.repo_url,
                "platform": request.platform or (remote.platform if remote else None),
                "branch": request.branch or "main",
            },
        )

    # Persist connector config in PostgreSQL + clone path
    if request.workspace_id and request.workspace_name:
        remote = provider.remote_for(resource_id)
        clone_path = str(remote.clone_path) if remote and remote.clone_path else ""
        from ecms.persistence.database.rest_session import db_session as pg_sess
        from ecms.persistence.repositories.project import ProjectRepository
        async with pg_sess() as s:
            repo = ProjectRepository(s)
            await repo.upsert(
                project_id=f"proj:{request.workspace_id}",
                workspace_id=request.workspace_id,
                name=request.workspace_name,
                connectors=[{
                    "type": "git",
                    "config": {
                        "repo_url": request.repo_url,
                        "platform": request.platform or "",
                        "branch": request.branch or "main",
                    },
                    "persist_path": clone_path,
                }],
            )

    try:
        async with orchestrator_context(request.persist) as orchestrator:
            all_episodes, write_result = await orchestrator.process_batch(ukos)
            episode_count = len(all_episodes)
            remote = provider.remote_for(resource_id)
            await snapshot_after_graph_write(
                persisted=request.persist,
                success_count=write_result.success_count,
                source="git",
                revision=resource_id,
            )
            # Trigger AI categorization (background, non-blocking)
            if request.workspace_id:
                asyncio.create_task(run_categorization(request.workspace_id, request.workspace_id))
            return GitSyncResponse(
                provider="git",
                platform=remote.platform,
                repo_url=remote.repo_url,
                resource_id=resource_id,
                uko_count=len(ukos),
                episode_count=episode_count,
                persisted=request.persist,
                write_success_count=write_result.success_count,
                write_failure_count=write_result.failure_count,
                write_errors=[f"{f.node_id}: [{f.stage}] {f.error_message}" for f in write_result.failures],
            )
    except Exception as exc:
        import traceback
        raise HTTPException(
            status_code=500,
            detail=f"Graph persistence failed: {exc}. Trace: {traceback.format_exc()}",
        ) from exc


@router.post("/mysql/sync", response_model=MySQLSyncResponse)
async def sync_mysql_database(request: MySQLSyncRequest) -> MySQLSyncResponse:
    provider = MySQLProvider()
    await provider.authenticate(
        {
            "host": request.host,
            "port": request.port,
            "user": request.user,
            "password": request.password.get_secret_value(),
            "database": request.database,
            "connect_timeout": request.connect_timeout,
        }
    )
    ukos = [uko async for uko in provider.sync(request.database)]
    if request.workspace_id:
        ukos = attach_ukos_to_workspace(ukos, request.workspace_id, request.workspace_name)
        _persist_connector(
            request.workspace_id,
            {
                "type": "mysql",
                "key": request.host,
                "host": request.host,
                "port": request.port,
                "user": request.user,
                "database": request.database,
            },
        )
        await _db_upsert_connector(
            request.workspace_id,
            request.workspace_name or request.workspace_id,
            "mysql",
            {
                "host": request.host,
                "port": str(request.port),
                "database": request.database,
            },
        )

    try:
        async with orchestrator_context(request.persist) as orchestrator:
            all_episodes, write_result = await orchestrator.process_batch(ukos)
            episode_count = len(all_episodes)
            await snapshot_after_graph_write(
                persisted=request.persist,
                success_count=write_result.success_count,
                source="mysql",
                revision=request.database,
            )
            return MySQLSyncResponse(
                provider="mysql",
                database=request.database,
                uko_count=len(ukos),
                episode_count=episode_count,
                persisted=request.persist,
                write_success_count=write_result.success_count,
                write_failure_count=write_result.failure_count,
                write_errors=[f"{f.node_id}: [{f.stage}] {f.error_message}" for f in write_result.failures],
            )
    except Exception as exc:
        import traceback
        raise HTTPException(
            status_code=500,
            detail=f"Graph persistence failed: {exc}. Trace: {traceback.format_exc()}",
        ) from exc
