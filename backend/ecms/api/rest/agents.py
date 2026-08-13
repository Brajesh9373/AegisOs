"""Agent management REST API."""

from __future__ import annotations

from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ecms.persistence.database.rest_session import db_session
from ecms.persistence.repositories.agent import AgentRepository
from ecms.persistence.repositories.project_agent_position import ProjectAgentPositionRepository

router = APIRouter(prefix="/agents", tags=["agents"])


async def _require_auth(request: Request) -> dict:
    """Validate Bearer token via auth_sessions table."""
    from sqlalchemy import text

    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    async with db_session() as session:
        row = (await session.execute(
            text("SELECT * FROM auth_sessions WHERE token = :token"),
            {"token": token},
        )).first()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid session")
        sess = row._mapping if hasattr(row, "_mapping") else dict(row)
        if int(sess.get("expiresat", "0")) < int(datetime.now().timestamp() * 1000):
            raise HTTPException(status_code=401, detail="Session expired")
        user_row = (await session.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": sess["userid"]},
        )).first()
        if not user_row:
            raise HTTPException(status_code=401, detail="User not found")
        return dict(user_row._mapping) if hasattr(user_row, "_mapping") else dict(user_row)


class CreateAgentRequest(BaseModel):
    id: str
    name: str
    role: str
    designation: str = ""
    department: str
    role_description: str | None = None
    skills: list | None = None
    reports_to: str | None = None
    tool_policy: dict | None = None
    workspace_scope: dict | None = None
    system_prompt_addon: str | None = None
    certificates: list | None = None


class AssignAgentRequest(BaseModel):
    position_id: str


class HireForPositionRequest(BaseModel):
    position_id: str
    name: str | None = None
    role: str | None = None
    department: str | None = None
    role_description: str | None = None
    skills: list[str] | None = None
    reports_to: str | None = None


class UpdateAgentRequest(BaseModel):
    name: str | None = None
    role: str | None = None
    designation: str | None = None
    role_description: str | None = None
    skills: list | None = None
    department: str | None = None
    reports_to: str | None = None
    tool_policy: dict | None = None
    workspace_scope: dict | None = None
    system_prompt_addon: str | None = None
    status: str | None = None
    certificates: list | None = None


@router.get("")
async def list_agents(request: Request):
    await _require_auth(request)
    async with db_session() as s:
        repo = AgentRepository(s)
        agents = await repo.list_all()
        return [a.to_dict() for a in agents]


@router.get("/tree")
async def org_chart(request: Request):
    await _require_auth(request)
    async with db_session() as s:
        repo = AgentRepository(s)
        return await repo.get_org_tree()


@router.get("/available")
async def list_available_agents(request: Request):
    """Active reusable agents eligible for project staffing."""
    await _require_auth(request)
    async with db_session() as s:
        repo = AgentRepository(s)
        agents = await repo.list_available()
        return [a.to_dict() for a in agents]


@router.get("/available/tree")
async def available_agent_tree(request: Request):
    """Hierarchy of active reusable agents."""
    await _require_auth(request)
    async with db_session() as s:
        repo = AgentRepository(s)
        return await repo.get_available_tree()


@router.get("/available/designations")
async def available_designations(request: Request):
    """Count active reusable agents grouped by designation."""
    await _require_auth(request)
    async with db_session() as s:
        repo = AgentRepository(s)
        return await repo.count_available_by_designation()


@router.post("/{agent_id}/assign")
async def assign_agent(agent_id: str, body: AssignAgentRequest, request: Request):
    """Assign a reusable agent to a project position."""
    await _require_auth(request)
    async with db_session() as s:
        repo = ProjectAgentPositionRepository(s)
        position = await repo.get(body.position_id)
        if not position:
            raise HTTPException(status_code=404, detail="Project agent position not found")
        assignment = await repo.assign(body.position_id, agent_id, assigned_by_user_id="current-user")
        if not assignment:
            raise HTTPException(status_code=404, detail="Active agent not found")
        positions = await repo.serialize_project(position.project_id)
        return {
            "assignment": assignment.to_dict(),
            "positions": positions,
        }


@router.post("/{agent_id}/unassign")
async def unassign_agent(agent_id: str, request: Request):
    """Legacy endpoint: permanent agents are reusable, so no pool mutation is needed."""
    await _require_auth(request)
    async with db_session() as s:
        repo = AgentRepository(s)
        agent = await repo.unassign_from_project(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent.to_dict()


@router.post("/hire-for-position")
async def hire_for_position(body: HireForPositionRequest, request: Request):
    """Hire a permanent certified agent for a vacant project position and assign it."""
    await _require_auth(request)
    async with db_session() as s:
        agent_repo = AgentRepository(s)
        position_repo = ProjectAgentPositionRepository(s)
        position = await position_repo.get(body.position_id)
        if not position:
            raise HTTPException(status_code=404, detail="Project agent position not found")

        reports_to = body.reports_to
        if not reports_to and position.reports_to:
            from ecms.persistence.models.project_agent_position import ProjectAgentAssignment

            parent_assignment = await s.get(ProjectAgentAssignment, position.reports_to)
            reports_to = parent_assignment.agent_id if parent_assignment else None

        designation = position.designation or body.role or position.role
        agent_id = f"agent-{uuid.uuid4().hex[:12]}"
        agent = await agent_repo.create(
            id=agent_id,
            name=body.name or f"{designation} Agent",
            role=body.role or position.role or "agent",
            designation=designation,
            department=body.department or position.department or "delivery",
            role_description=body.role_description or position.role_description,
            skills=body.skills if body.skills is not None else (position.skills or []),
            reports_to=reports_to,
            tool_policy=position.tool_policy or {},
            system_prompt_addon=position.system_prompt_addon,
            status="active",
            model=position.model,
        )
        assignment = await position_repo.assign(position.id, agent.id, assigned_by_user_id="current-user")
        positions = await position_repo.serialize_project(position.project_id)
        return {
            "agent": agent.to_dict(),
            "assignment": assignment.to_dict() if assignment else None,
            "positions": positions,
        }


@router.get("/{agent_id}")
async def get_agent(agent_id: str, request: Request):
    await _require_auth(request)
    async with db_session() as s:
        repo = AgentRepository(s)
        agent = await repo.get(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        data = agent.to_dict()
        reports = await repo.list_by_manager(agent_id)
        data["reports"] = [r.to_dict() for r in reports]
        return data


@router.post("")
async def create_agent(body: CreateAgentRequest, request: Request):
    await _require_auth(request)
    async with db_session() as s:
        repo = AgentRepository(s)
        existing = await repo.get(body.id)
        if existing:
            raise HTTPException(status_code=409, detail="Agent ID already exists")
        kwargs = body.model_dump()
        agent = await repo.create(**kwargs)
        return agent.to_dict()


@router.put("/{agent_id}")
async def update_agent(agent_id: str, body: UpdateAgentRequest, request: Request):
    await _require_auth(request)
    async with db_session() as s:
        repo = AgentRepository(s)
        kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
        agent = await repo.update(agent_id, **kwargs)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent.to_dict()


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, request: Request):
    await _require_auth(request)
    async with db_session() as s:
        repo = AgentRepository(s)
        deleted = await repo.delete(agent_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"deleted": True, "agent_id": agent_id}
