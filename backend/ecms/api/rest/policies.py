"""Access policy management REST API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ecms.persistence.database.rest_session import db_session

router = APIRouter(prefix="/policies", tags=["policies"])


class CreatePolicyRequest(BaseModel):
    name: str
    effect: str
    department: str | None = None
    role_level_min: int | None = None
    resource_type: str | None = None
    path_pattern: str | None = None
    source_type: str | None = None
    resource_attrs: dict | None = None
    action: str
    priority: int = 100
    created_by: str | None = None


@router.get("")
async def list_policies():
    from sqlalchemy import select
    from ecms.persistence.models.access_policy import AccessPolicy

    async with db_session() as s:
        stmt = select(AccessPolicy).order_by(AccessPolicy.priority.asc())
        result = await s.execute(stmt)
        return [p.to_dict() for p in result.scalars().all()]


@router.post("")
async def create_policy(body: CreatePolicyRequest):
    from ecms.persistence.models.access_policy import AccessPolicy
    import uuid

    async with db_session() as s:
        policy = AccessPolicy(
            id=f"pol-{uuid.uuid4().hex[:12]}",
            name=body.name,
            effect=body.effect,
            department=body.department,
            role_level_min=body.role_level_min,
            resource_type=body.resource_type,
            path_pattern=body.path_pattern,
            source_type=body.source_type,
            resource_attrs=body.resource_attrs or {},
            action=body.action,
            priority=body.priority,
            created_by=body.created_by,
        )
        s.add(policy)
        await s.flush()
        return policy.to_dict()


@router.delete("/{policy_id}")
async def delete_policy(policy_id: str):
    from sqlalchemy import select, delete
    from ecms.persistence.models.access_policy import AccessPolicy

    async with db_session() as s:
        stmt = select(AccessPolicy).where(AccessPolicy.id == policy_id)
        result = await s.execute(stmt)
        policy = result.scalar_one_or_none()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        await s.delete(policy)
        await s.flush()
        return {"deleted": True, "policy_id": policy_id}


@router.get("/recommendations")
async def list_recommendations():
    from sqlalchemy import select
    from ecms.persistence.models.access_policy import PolicyRecommendation

    async with db_session() as s:
        stmt = select(PolicyRecommendation).order_by(PolicyRecommendation.created_at.desc())
        result = await s.execute(stmt)
        return [r.to_dict() for r in result.scalars().all()]


@router.post("/recommendations")
async def trigger_recommendation(project_id: str = Query(...)):
    """Trigger analysis. Returns immediately with a task ID. Agent runs in background."""
    import asyncio
    from ecms.agent.policy_agent import recommend_policies_for_project

    task_id = f"policy-analysis-{project_id}"

    # Check if one is already running
    existing = _running_tasks.get(task_id)
    if existing and not existing.done():
        return {"status": "already_running", "task_id": task_id}

    async def _run():
        try:
            await recommend_policies_for_project(project_id)
        except Exception as e:
            import logging
            logging.getLogger("ecms.agent").warning("Policy analysis failed: %s", e)
        finally:
            # Allow re-triggering
            _running_tasks.pop(task_id, None)

    task = asyncio.create_task(_run())
    _running_tasks[task_id] = task
    return {"status": "started", "task_id": task_id, "message": "Analysis running in background. Refresh recommendations in ~60 seconds."}


_running_tasks: dict[str, asyncio.Task] = {}


@router.post("/recommendations/{rec_id}/approve")
async def approve_recommendation(rec_id: str, reviewer_id: str = Query("agent-cto")):
    from ecms.agent.policy_agent import approve_recommendation as approve
    return await approve(rec_id, reviewer_id)
