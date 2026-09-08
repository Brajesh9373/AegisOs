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
import re
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
    project_id: str | None = None


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
    project_id: str | None = None
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
    project_id: str | None = None


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


async def _ensure_memory_bridge(request: Request | None = None) -> None:
    """Attach the ECMS memory bridge to the session manager (idempotent).

    With a request, reads the app's shared cognitive system. Without one
    (background tasks like project team spawn), builds minimal engines over
    an in-memory index — episodic recall still works via DB backfill.
    Silent no-op when the manager already has a bridge.
    """
    manager = get_session_manager()
    if manager.memory_bridge is not None:
        return
    cognitive = getattr(request.app.state, "cognitive", None) if request is not None else None
    from ecms.agent_os.runtime.agent_memory import AgentMemoryBridge

    if cognitive is not None:
        manager.memory_bridge = AgentMemoryBridge(
            memory=cognitive.memory, repository=cognitive.repository
        )
    else:
        from ecms.infrastructure.reasoning.deterministic import DeterministicEmbeddingProvider
        from ecms.knowledge.infrastructure.repository import InMemoryKnowledgeRepository
        from ecms.memory.services.engine import DefaultMemoryEngine

        embedder = DeterministicEmbeddingProvider()
        repository = InMemoryKnowledgeRepository(embedder)
        manager.memory_bridge = AgentMemoryBridge(
            memory=DefaultMemoryEngine(repository, embedder=embedder),
            repository=repository,
        )
    await manager.memory_bridge.backfill_from_db()


def get_team_for_project(project_id: str) -> TeamRecord | None:
    """Return the live team bound to a project, if any.

    Teams whose members all died are stopped and deregistered so the next
    call spawns fresh.
    """
    manager = get_session_manager()
    for team in list(_TEAMS.values()):
        if team.project_id != project_id:
            continue
        alive = [
            m.agent_id for m in team.members
            if (s := manager.sessions.get(m.agent_id)) is not None and s.status != "dead"
        ]
        if alive:
            return team
    return None


async def prune_dead_project_team(project_id: str) -> None:
    """Stop and deregister a project team with no live members (best-effort)."""
    manager = get_session_manager()
    for team in list(_TEAMS.values()):
        if team.project_id != project_id:
            continue
        alive = any(
            (s := manager.sessions.get(m.agent_id)) is not None and s.status != "dead"
            for m in team.members
        )
        if not alive:
            try:
                await manager.stop_team([m.agent_id for m in team.members])
            except Exception:
                pass
            _TEAMS.pop(team.team_id, None)


async def spawn_team_for_project(
    project_id: str, handoff: str | None = None
) -> TeamInfo:
    """Get-or-create the DSH engineering team for a project.

    Spawning is concurrent (~2s); the BA handoff brief is queued to the HOE
    without waiting, so callers never block on an LLM run.
    """
    import logging as _logging

    _logger = _logging.getLogger("ecms.api.hierarchy")
    await _ensure_memory_bridge(None)
    manager = get_session_manager()
    await manager.ensure_started()

    await prune_dead_project_team(project_id)
    existing = get_team_for_project(project_id)
    if existing is not None:
        return TeamInfo(
            team_id=existing.team_id,
            created_at=existing.created_at,
            project_id=existing.project_id,
            agents=[
                _agent_info(manager, m.profile_id, m.agent_id)
                for m in existing.members
                if m.agent_id in manager.sessions
            ],
        )

    short = project_id[:8]
    members = [
        TeamMemberSpec(profile_id=p, agent_id=f"{a}-{short}")
        for p, a in DEFAULT_TEAM
    ]
    team_id = f"team-proj-{short}-{uuid.uuid4().hex[:6]}"
    specs = [(m.profile_id, m.agent_id) for m in members]
    await manager.spawn_team_from_profiles(
        specs,
        api_key=_api_key(),
        extra_system_prompt=(
            f"You are working on project {project_id}. "
            "Coordinate with your fellow team members through your team lead."
        ),
    )
    _TEAMS[team_id] = TeamRecord(
        team_id=team_id, created_at=time.time(), members=members, project_id=project_id
    )
    _logger.info("Spawned DSH team %s for project %s", team_id, project_id)

    if handoff:
        hoe_id = next(
            (m.agent_id for m in members if m.profile_id == "head-of-engineering"),
            members[0].agent_id,
        )
        queued = await manager.ingest_message(
            hoe_id,
            AgentMessage(
                source="system",
                sender_id="ba-handoff",
                sender_name="BA Handoff",
                content=handoff,
                channel_id=f"project-{project_id}",
                metadata={"type": "ba_handoff", "project_id": project_id},
            ),
        )
        if not queued:
            _logger.warning("HOE %s not accepting handoff for project %s", hoe_id, project_id)

    return TeamInfo(
        team_id=team_id,
        created_at=_TEAMS[team_id].created_at,
        project_id=project_id,
        agents=[_agent_info(manager, m.profile_id, m.agent_id) for m in members],
    )


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

    _TEAMS[team_id] = TeamRecord(
        team_id=team_id,
        created_at=time.time(),
        members=members,
        project_id=body.project_id,
    )
    return TeamInfo(
        team_id=team_id,
        created_at=_TEAMS[team_id].created_at,
        project_id=body.project_id,
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
        result.append(TeamInfo(team_id=team.team_id, created_at=team.created_at, project_id=team.project_id, agents=agents))
    return result


class SpawnForProjectRequest(BaseModel):
    project_id: str
    handoff: str | None = None


class KickoffRequest(BaseModel):
    brief: str | None = None
    timeout_each: float = Field(default=300.0, le=900.0)


class KickoffDelegation(BaseModel):
    label: str
    task: str
    to_agent: str
    response: str | None


class KickoffResponse(BaseModel):
    team_id: str
    project_id: str
    breakdown: str
    delegations: list[KickoffDelegation]
    review_note: str


@router.post("/teams/spawn-for-project", response_model=TeamInfo)
async def spawn_for_project(body: SpawnForProjectRequest) -> TeamInfo:
    """Get-or-create the DSH team for a project, with an optional HOE brief."""
    try:
        return await spawn_team_for_project(body.project_id, handoff=body.handoff)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project team spawn failed: {e}")


def _parse_kickoff_tasks(breakdown: str) -> list[tuple[str, str]]:
    """Extract (FRONTEND|BACKEND, task) pairs from an HOE breakdown.

    Expected line format: `FRONTEND: do X` / `BACKEND: do Y`. Lines in any
    other shape are ignored (the caller falls back to broadcast).
    """
    tasks = []
    for line in breakdown.splitlines():
        match = re.match(r"^\s*(FRONTEND|BACKEND)\s*:\s*(.+?)\s*$", line)
        if match:
            tasks.append((match.group(1), match.group(2)))
    return tasks[:4]


async def kickoff_project_team(
    project_id: str, brief: str | None = None, timeout_each: float = 300.0
) -> KickoffResponse:
    """Autonomously start project execution: breakdown, delegate, review.

    1. Ensures the project team exists (spawning with the brief as handoff
       when it does not).
    2. Asks the HOE to break the work into FRONTEND/BACKEND-labeled tasks.
    3. Delegates each task to the matching engineer in parallel.
    4. Reports the outcomes back to the HOE for review.
    """
    import logging as _logging

    _logger = _logging.getLogger("ecms.api.hierarchy")
    await _ensure_memory_bridge(None)
    manager = get_session_manager()
    await manager.ensure_started()

    team = get_team_for_project(project_id)
    if team is None:
        team = (await spawn_team_for_project(project_id, handoff=brief)).team_id
        team = get_team_for_project(project_id)
        if team is None:  # pragma: no cover - defensive
            raise RuntimeError(f"Team spawn did not register for project {project_id}")
    team_id = team.team_id
    by_profile = {m.profile_id: m.agent_id for m in team.members}
    hoe_id = by_profile.get("head-of-engineering")
    fe_id = next((a for p, a in by_profile.items() if "frontend" in p), None)
    be_id = next((a for p, a in by_profile.items() if "backend" in p), None)
    if hoe_id is None or fe_id is None or be_id is None:
        raise RuntimeError(f"Team {team_id} is missing HOE/frontend/backend members")

    brief_block = f"\nProject brief:\n{brief}\n" if brief else "\n"
    breakdown_prompt = (
        "Split the project work below into 2-4 concrete implementation tasks "
        "and assign each to one engineer. Your reply must contain ONLY task "
        "lines in exactly this format, one per line, nothing else:\n"
        "FRONTEND: <task for the frontend engineer>\n"
        "BACKEND: <task for the backend engineer>\n"
        "Example:\n"
        "FRONTEND: Build the status page layout with service health cards\n"
        "BACKEND: Create the GET /health API returning service statuses"
        f"{brief_block}"
    )
    reformat_prompt = (
        "Reformat your task list now. Reply with ONLY lines in exactly "
        "this format, one per line, no other text:\n"
        "FRONTEND: <task>\nBACKEND: <task>"
    )
    breakdown, parsed = "", []
    # Up to two breakdown attempts, always with the full prompt: a rotated
    # session never saw the brief in its DSH log (platform memory still
    # injects past episodes). An ERROR run means no text at all — often a
    # malformed tool call poisoning that session's replay — so rotate to a
    # clean session and retry. A conversational (unparseable but real) answer
    # gets one reformat follow-up instead.
    for _ in range(2):
        breakdown, _ = await send_message_to_agent(
            team_id, hoe_id, breakdown_prompt,
            sender_name="Kickoff", timeout=timeout_each,
        )
        if breakdown.startswith("ERROR:"):
            _logger.warning(
                "Kickoff breakdown errored for %s; rotating session", project_id
            )
            manager.rotate_session(hoe_id)
            continue
        parsed = _parse_kickoff_tasks(breakdown)
        if parsed:
            break
        _logger.info(
            "Kickoff breakdown unparseable for %s; requesting reformat", project_id
        )
        breakdown, _ = await send_message_to_agent(
            team_id,
            hoe_id,
            reformat_prompt,
            sender_name="Kickoff",
            timeout=min(timeout_each, 120.0),
        )
        parsed = _parse_kickoff_tasks(breakdown)
        break
    if breakdown.startswith("ERROR:"):
        raise RuntimeError(f"HOE breakdown failed: {breakdown}")
    targets = {"FRONTEND": fe_id, "BACKEND": be_id}
    assignments = [(targets[label], task) for label, task in parsed if label in targets]
    if not assignments:
        _logger.warning("Kickoff breakdown unparseable for %s; broadcasting", project_id)
        fallback_task = (
            "Start on the highest-priority work you own for this project. "
            "Report what you did and what remains."
            f"{brief_block}\nHOE notes:\n{breakdown}"
        )
        results = await asyncio.gather(
            *[manager.delegate_task(hoe_id, aid, fallback_task, timeout=timeout_each)
              for aid in (fe_id, be_id)],
            return_exceptions=True,
        )
        delegations = [
            KickoffDelegation(
                label="BROADCAST", task=fallback_task[:200],
                to_agent=aid,
                response=None if isinstance(res, Exception) else res,
            )
            for aid, res in zip((fe_id, be_id), results)
        ]
    else:
        results = await asyncio.gather(
            *[manager.delegate_task(hoe_id, aid, task, timeout=timeout_each)
              for aid, task in assignments],
            return_exceptions=True,
        )
        delegations = [
            KickoffDelegation(
                label="FRONTEND" if aid == fe_id else "BACKEND",
                task=task[:200],
                to_agent=aid,
                response=None if isinstance(res, Exception) else res,
            )
            for (aid, task), res in zip(assignments, results)
        ]

    review_lines = [
        f"- {d.label} ({d.to_agent}): {(d.response or 'no response')[:300]}"
        for d in delegations
    ]
    review_note = (
        "Teammates reported back on the kickoff tasks:\n" + "\n".join(review_lines)
        + "\nReply briefly: what is done, what remains, and your next move."
    )
    await manager.ingest_message(
        hoe_id,
        AgentMessage(
            source="system", sender_id="kickoff", sender_name="Kickoff",
            content=review_note, channel_id=f"project-{project_id}",
            metadata={"type": "kickoff_review", "project_id": project_id},
        ),
    )
    return KickoffResponse(
        team_id=team_id, project_id=project_id, breakdown=breakdown,
        delegations=delegations, review_note=review_note,
    )


@router.post("/teams/by-project/{project_id}/kickoff", response_model=KickoffResponse)
async def kickoff_team(project_id: str, body: KickoffRequest) -> KickoffResponse:
    """Autonomously start a bound project team (breakdown, delegate, review)."""
    try:
        return await kickoff_project_team(
            project_id, brief=body.brief, timeout_each=body.timeout_each
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project kickoff failed: {e}")


@router.get("/teams/by-project/{project_id}", response_model=TeamInfo)
async def get_team_by_project(project_id: str) -> TeamInfo:
    """Get the live DSH team bound to a project (404 when none)."""
    manager = get_session_manager()
    team = get_team_for_project(project_id)
    if team is None:
        raise HTTPException(status_code=404, detail=f"No live team for project {project_id}")
    return TeamInfo(
        team_id=team.team_id,
        created_at=team.created_at,
        project_id=team.project_id,
        agents=[
            _agent_info(manager, m.profile_id, m.agent_id)
            for m in team.members
            if m.agent_id in manager.sessions
        ],
    )


@router.get("/teams/{team_id}", response_model=TeamInfo)
async def get_team(team_id: str) -> TeamInfo:
    """Get one team with current per-agent status."""
    manager = get_session_manager()
    team = _team_or_404(team_id)
    return TeamInfo(
        team_id=team.team_id,
        created_at=team.created_at,
        project_id=team.project_id,
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
    response, duration = await send_message_to_agent(
        team_id,
        body.agent_id,
        body.content,
        sender_name=body.sender_name,
        timeout=body.timeout,
    )
    return MessageResponse(
        team_id=team_id,
        agent_id=body.agent_id,
        response=response,
        duration_ms=int(duration * 1000),
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


@router.get("/memory/search")
async def search_memory(
    query: str, request: Request, agent_id: str = "", limit: int = 3
) -> dict:
    """Agent-initiated episodic search (backs the memory_search_episodes DSH tool)."""
    await _ensure_memory_bridge(request)
    bridge = _bridge_or_400(request)
    results = await bridge.search_episodes(query, limit=limit)
    return {"results": [f"{r['display_name']}: {r['description']}" for r in results]}


async def send_message_to_agent(
    team_id: str,
    agent_id: str,
    content: str,
    *,
    sender_name: str = "AegisOS",
    timeout: float = 180.0,
) -> tuple[str, float]:
    """Send a message to a team member and wait for its AI response.

    Shared by the HTTP endpoint and server-side callers (workspace chat).
    Returns (response_text, duration_seconds). Raises HTTPException when the
    agent is missing, gone, or silent past the timeout.
    """
    manager = get_session_manager()
    team = _team_or_404(team_id)
    if agent_id not in {m.agent_id for m in team.members}:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} is not in team {team_id}")
    message = AgentMessage(
        source="aegisos",
        sender_id="aegisos",
        sender_name=sender_name,
        content=content,
        channel_id=f"team-{team_id}",
    )
    waiter = asyncio.create_task(_wait_for_reply(manager, agent_id, timeout))
    queued = await manager.ingest_message(agent_id, message)
    if not queued:
        waiter.cancel()
        raise HTTPException(status_code=410, detail=f"Agent {agent_id} is no longer running")
    started = time.time()
    try:
        response = await waiter
    except HTTPException:
        raise
    return response, time.time() - started
