"""Agent Hierarchy API — live HOE-led engineering teams over DSH SDK sessions.

Exposes the persistent-agent hierarchy (Head of Engineering delegating to
senior Frontend/Backend engineers) to the frontend:

- POST   /api/hierarchy/teams — spawn a team from AgentProfiles (concurrent)
- GET    /api/hierarchy/teams — list live teams
- GET    /api/hierarchy/teams/{team_id} — per-agent status
- DELETE /api/hierarchy/teams/{team_id} — stop a team
- POST   /api/hierarchy/teams/{team_id}/messages — send a message to one
  agent and long-poll (up to `timeout` seconds) for its AI response
- POST   /api/hierarchy/teams/{team_id}/delegate — parent delegates a task
  to a child agent and waits for the result

Teams are tracked in memory (single-process, like the chat fallback store);
each agent keeps one persistent `dsh --profile sdk` subprocess with a durable
DSH session, so memory survives across messages within the process lifetime.
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from dataclasses import dataclass, field

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ecms.agent_os.runtime.dsh_sdk_manager import (
    AgentMessage,
    get_session_manager,
)

router = APIRouter(prefix="/api/hierarchy", tags=["hierarchy"])

DEFAULT_TEAM = [
    ("head-of-engineering", "hoe-1"),
    ("senior-frontend-engineer", "frontend-1"),
    ("senior-backend-engineer", "backend-1"),
]


# ── Models ────────────────────────────────────────────────────────────────

class TeamMemberSpec(BaseModel):
    profile_id: str
    agent_id: str


class CreateTeamRequest(BaseModel):
    members: list[TeamMemberSpec] = Field(
        default_factory=lambda: [TeamMemberSpec(profile_id=p, agent_id=a) for p, a in DEFAULT_TEAM]
    )
    extra_system_prompt: str | None = None


class AgentInfo(BaseModel):
    agent_id: str
    profile_id: str
    role: str
    session_id: str
    pid: int | None
    status: str


class TeamInfo(BaseModel):
    team_id: str
    created_at: float
    agents: list[AgentInfo]


class SendMessageRequest(BaseModel):
    agent_id: str
    content: str
    sender_name: str = "AegisOS"
    timeout: float = Field(default=180.0, le=600.0)


class MessageResponse(BaseModel):
    team_id: str
    agent_id: str
    response: str
    duration_ms: int


class DelegateRequest(BaseModel):
    from_agent: str
    to_agent: str
    task: str
    timeout: float = Field(default=300.0, le=900.0)


class DelegateResponse(BaseModel):
    team_id: str
    from_agent: str
    to_agent: str
    response: str | None
    duration_ms: int


class AgentStatusResponse(BaseModel):
    agent_id: str
    status: str
    pending_messages: int
    active_requests: int
    session_id: str
    last_heartbeat: float


# ── Team store (single-process) ───────────────────────────────────────────

@dataclass
class TeamRecord:
    team_id: str
    created_at: float
    members: list[TeamMemberSpec] = field(default_factory=list)


_TEAMS: dict[str, TeamRecord] = {}


def _api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not configured on the server")
    return key


def _team_or_404(team_id: str) -> TeamRecord:
    team = _TEAMS.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    return team


async def _ensure_memory_bridge(request: Request) -> None:
    """Attach the ECMS memory bridge to the session manager (idempotent).

    Reads the app's shared cognitive system (knowledge + memory engines) so
    agent prompts recall platform memory and responses are recorded back as
    episodic UCOs. On first attach, persisted episodes are backfilled from
    the database so recall survives backend restarts. Silent no-op outside
    the full app (tests, scripts) where the manager simply runs on DSH
    session memory.
    """
    manager = get_session_manager()
    if manager.memory_bridge is not None:
        return
    cognitive = getattr(request.app.state, "cognitive", None)
    if cognitive is None:
        return
    from ecms.agent_os.runtime.agent_memory import AgentMemoryBridge
    bridge = AgentMemoryBridge(
        memory=cognitive.memory, repository=cognitive.repository
    )
    manager.memory_bridge = bridge
    await bridge.backfill_from_db()


def _agent_info(manager, profile_id: str, agent_id: str) -> AgentInfo:
    session = manager.sessions.get(agent_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} is not running")
    return AgentInfo(
        agent_id=agent_id,
        profile_id=profile_id,
        role=session.role,
        session_id=session.session_id,
        pid=session.process.pid if session.process else None,
        status=session.status,
    )


async def _wait_for_reply(manager, agent_id: str, timeout: float) -> str:
    """Register a one-shot response callback and wait for the agent's reply."""
    session = manager.sessions.get(agent_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} is not running")
    loop = asyncio.get_running_loop()
    future: asyncio.Future[str] = loop.create_future()

    async def _capture(response: str, _message: AgentMessage) -> None:
        if not future.done():
            future.set_result(response)

    session.on_response(_capture)
    try:
        return await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail=f"Agent {agent_id} did not respond in {timeout}s")
    finally:
        try:
            session._response_callbacks.remove(_capture)
        except ValueError:
            pass


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post("/teams", response_model=TeamInfo)
async def create_team(request: Request, body: CreateTeamRequest) -> TeamInfo:
    """Spawn a live engineering team (HOE + engineers) from AgentProfiles."""
    await _ensure_memory_bridge(request)
    manager = get_session_manager()
    await manager.ensure_started()
    team_id = f"team-{uuid.uuid4().hex[:8]}"
    prefix = team_id + "-"
    members = [
        TeamMemberSpec(profile_id=m.profile_id, agent_id=prefix + m.agent_id)
        for m in body.members
    ]
    specs = [(m.profile_id, m.agent_id) for m in members]
    try:
        await manager.spawn_team_from_profiles(
            specs,
            api_key=_api_key(),
            extra_system_prompt=body.extra_system_prompt,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Team spawn failed: {e}")

    _TEAMS[team_id] = TeamRecord(team_id=team_id, created_at=time.time(), members=members)
    return TeamInfo(
        team_id=team_id,
        created_at=_TEAMS[team_id].created_at,
        agents=[_agent_info(manager, m.profile_id, m.agent_id) for m in members],
    )


@router.get("/teams", response_model=list[TeamInfo])
async def list_teams() -> list[TeamInfo]:
    """List live teams with current agent info."""
    manager = get_session_manager()
    result = []
    for team in _TEAMS.values():
        agents = []
        for m in team.members:
            session = manager.sessions.get(m.agent_id)
            if session:
                agents.append(_agent_info(manager, m.profile_id, m.agent_id))
        result.append(TeamInfo(team_id=team.team_id, created_at=team.created_at, agents=agents))
    return result


@router.get("/teams/{team_id}", response_model=TeamInfo)
async def get_team(team_id: str) -> TeamInfo:
    """Get one team with current per-agent status."""
    manager = get_session_manager()
    team = _team_or_404(team_id)
    return TeamInfo(
        team_id=team.team_id,
        created_at=team.created_at,
        agents=[_agent_info(manager, m.profile_id, m.agent_id) for m in team.members],
    )


@router.delete("/teams/{team_id}")
async def delete_team(team_id: str) -> dict:
    """Stop every agent in a team and deregister it."""
    manager = get_session_manager()
    team = _team_or_404(team_id)
    await manager.stop_team([m.agent_id for m in team.members])
    del _TEAMS[team_id]
    return {"team_id": team_id, "stopped": True}


@router.post("/teams/{team_id}/messages", response_model=MessageResponse)
async def send_message(team_id: str, body: SendMessageRequest, request: Request) -> MessageResponse:
    """Send a message to one team member and wait for its AI response."""
    await _ensure_memory_bridge(request)
    manager = get_session_manager()
    team = _team_or_404(team_id)
    if body.agent_id not in {m.agent_id for m in team.members}:
        raise HTTPException(status_code=404, detail=f"Agent {body.agent_id} is not in team {team_id}")

    message = AgentMessage(
        source="aegisos",
        sender_id="aegisos-ui",
        sender_name=body.sender_name,
        content=body.content,
        channel_id=f"team-{team_id}",
    )
    waiter = asyncio.create_task(_wait_for_reply(manager, body.agent_id, body.timeout))
    queued = await manager.ingest_message(body.agent_id, message)
    if not queued:
        waiter.cancel()
        raise HTTPException(status_code=410, detail=f"Agent {body.agent_id} is no longer running")
    started = time.time()
    try:
        response = await waiter
    except HTTPException:
        raise
    return MessageResponse(
        team_id=team_id,
        agent_id=body.agent_id,
        response=response,
        duration_ms=int((time.time() - started) * 1000),
    )


@router.post("/teams/{team_id}/delegate", response_model=DelegateResponse)
async def delegate_task(team_id: str, body: DelegateRequest, request: Request) -> DelegateResponse:
    """Have one team member delegate a task to another and wait for the result."""
    await _ensure_memory_bridge(request)
    manager = get_session_manager()
    team = _team_or_404(team_id)
    member_ids = {m.agent_id for m in team.members}
    for aid in (body.from_agent, body.to_agent):
        if aid not in member_ids:
            raise HTTPException(status_code=404, detail=f"Agent {aid} is not in team {team_id}")
    started = time.time()
    try:
        response = await manager.delegate_task(
            from_agent=body.from_agent,
            to_agent=body.to_agent,
            task=body.task,
            timeout=body.timeout,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return DelegateResponse(
        team_id=team_id,
        from_agent=body.from_agent,
        to_agent=body.to_agent,
        response=response,
        duration_ms=int((time.time() - started) * 1000),
    )


@router.get("/teams/{team_id}/status", response_model=list[AgentStatusResponse])
async def team_status(team_id: str) -> list[AgentStatusResponse]:
    """Per-agent runtime status (queue depth, active requests, heartbeat)."""
    manager = get_session_manager()
    team = _team_or_404(team_id)
    result = []
    for m in team.members:
        status = await manager.get_delegation_status(m.agent_id)
        if "error" in status:
            raise HTTPException(status_code=404, detail=f"Agent {m.agent_id} is not running")
        result.append(AgentStatusResponse(**status))
    return result


# ── Memory layers ─────────────────────────────────────────────────────────

class LearnProcedureRequest(BaseModel):
    name: str
    description: str = ""
    steps: list[str]
    learned_by: str


class RememberRequest(BaseModel):
    key: str
    value: str
    agent_id: str
    shared: bool = False


class PublishPatternRequest(BaseModel):
    pattern_type: str
    description: str
    published_by: str


def _bridge_or_400(request: Request):
    manager = get_session_manager()
    bridge = manager.memory_bridge
    if bridge is None:
        raise HTTPException(
            status_code=400,
            detail="Memory bridge is not attached (no team spawned in this process yet)",
        )
    return bridge


@router.post("/procedures")
async def learn_procedure(body: LearnProcedureRequest, request: Request) -> dict:
    """Store a named multi-step workflow learned by an agent."""
    await _ensure_memory_bridge(request)
    bridge = _bridge_or_400(request)
    return await bridge.learn_procedure(body.name, body.description, body.steps, body.learned_by)


@router.get("/procedures")
async def recall_procedures(query: str, request: Request, limit: int = 3) -> list[dict]:
    """Find procedures matching a task description."""
    await _ensure_memory_bridge(request)
    return await _bridge_or_400(request).recall_procedures(query, limit=limit)


@router.post("/preferences")
async def remember_preference(body: RememberRequest, request: Request) -> dict:
    """Store a long-term preference (per-agent, or team-shared)."""
    await _ensure_memory_bridge(request)
    bridge = _bridge_or_400(request)
    await bridge.remember(body.key, body.value, body.agent_id, shared=body.shared)
    return {"key": body.key, "shared": body.shared, "stored": True}


@router.get("/preferences")
async def recall_preferences(agent_id: str, request: Request) -> dict[str, str]:
    """Return an agent's preferences (shared overlaid with its own)."""
    await _ensure_memory_bridge(request)
    return await _bridge_or_400(request).recall_preferences(agent_id)


@router.post("/patterns")
async def publish_pattern(body: PublishPatternRequest, request: Request) -> dict:
    """Publish a best practice / known bug / optimization / convention."""
    await _ensure_memory_bridge(request)
    bridge = _bridge_or_400(request)
    try:
        return await bridge.publish_pattern(
            body.pattern_type, body.description, body.published_by
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patterns")
async def search_patterns(query: str, request: Request, limit: int = 3) -> list[dict]:
    """Find org patterns matching a query."""
    await _ensure_memory_bridge(request)
    return await _bridge_or_400(request).search_patterns(query, limit=limit)
