"""Categorization trigger REST API."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query

router = APIRouter(prefix="/categorize", tags=["categorize"])


@router.post("")
async def trigger_categorization(
    workspace_id: str = Query(..., description="Workspace to categorize"),
    project_id: str | None = Query(None, description="Project for repo path lookup"),
):
    from ecms.agent.categorize import run_categorization

    asyncio.create_task(run_categorization(workspace_id, project_id))
    return {
        "status": "started",
        "message": f"Categorization queued for workspace {workspace_id}",
    }


@router.post("/sync")
async def categorize_after_sync(
    workspace_id: str = Query(...),
    project_id: str | None = Query(None),
):
    """Same as trigger but intended to be called programmatically after sync."""
    from ecms.agent.categorize import run_categorization

    asyncio.create_task(run_categorization(workspace_id, project_id))
    return {"status": "started", "workspace_id": workspace_id}
