"""Governance assignment REST API.

Endpoints for managing project-agent governance assignments:
which organization members own, monitor, or approve which project agents.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ecms.persistence.database.rest_session import db_session
from ecms.persistence.repositories.governance_assignment import GovernanceAssignmentRepository
from ecms.persistence.repositories.organization_member import OrganizationMemberRepository
from ecms.persistence.repositories.agent import AgentRepository

router = APIRouter(tags=["governance"])


class AssignAgentsRequest(BaseModel):
    project_id: str
    agent_ids: list[str]
    responsibility: str  # primary_owner | monitor | approver


class ChangeResponsibilityRequest(BaseModel):
    responsibility: str


class TransferOwnershipRequest(BaseModel):
    new_owner_member_id: str


# ── Member-centric assignment endpoints ───────────────────────────────


@router.get("/organization/members/{member_id}/assignments")
async def list_member_assignments(member_id: str):
    """List all governance assignments for a member or permanent agent."""
    async with db_session() as s:
        # Check organization_members first, then fall back to agents table
        member_repo = OrganizationMemberRepository(s)
        member = await member_repo.get(member_id)
        if not member:
            agent_repo = AgentRepository(s)
            agent = await agent_repo.get(member_id)
            if not agent:
                raise HTTPException(status_code=404, detail="Member not found")
        gov_repo = GovernanceAssignmentRepository(s)
        assignments = await gov_repo.list_by_member(member_id)
        result = []
        for a in assignments:
            d = a.to_dict()
            agent_repo = AgentRepository(s)
            agent = await agent_repo.get(a.project_agent_id)
            d["agent_name"] = agent.name if agent else a.project_agent_id
            d["agent_role"] = agent.role if agent else ""
            d["agent_designation"] = agent.designation if agent else ""
            result.append(d)
        return result


@router.post("/organization/members/{member_id}/assignments")
async def assign_agents(member_id: str, body: AssignAgentsRequest):
    """Bulk assign project agents to a member."""
    async with db_session() as s:
        member_repo = OrganizationMemberRepository(s)
        member = await member_repo.get(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        if member.status != "active":
            raise HTTPException(status_code=400, detail="Member is not active")

        # Validate responsibility
        if body.responsibility not in ("primary_owner", "monitor", "approver"):
            raise HTTPException(status_code=400, detail="Invalid responsibility type")

        agent_repo = AgentRepository(s)
        gov_repo = GovernanceAssignmentRepository(s)
        created = []
        errors = []

        for agent_id in body.agent_ids:
            # Validate agent exists and belongs to project
            agent = await agent_repo.get(agent_id)
            if not agent:
                errors.append({"agent_id": agent_id, "error": "Agent not found"})
                continue
            if agent.project_id != body.project_id:
                errors.append({"agent_id": agent_id, "error": "Agent does not belong to this project"})
                continue

            # Check for primary_owner conflict
            if body.responsibility == "primary_owner":
                existing_owner = await gov_repo.get_primary_owner(agent_id)
                if existing_owner and existing_owner.organization_member_id != member_id:
                    errors.append({
                        "agent_id": agent_id,
                        "error": f"Already owned by {existing_owner.organization_member_id}",
                        "existing_owner_id": existing_owner.organization_member_id,
                    })
                    continue

            # Check for duplicate
            existing = await gov_repo.list_by_agent(agent_id)
            duplicate = any(
                a.organization_member_id == member_id and a.responsibility == body.responsibility
                for a in existing
            )
            if duplicate:
                errors.append({"agent_id": agent_id, "error": "Assignment already exists"})
                continue

            assignment = await gov_repo.create(
                id=f"gov-{uuid.uuid4().hex[:12]}",
                organization_member_id=member_id,
                project_agent_id=agent_id,
                project_id=body.project_id,
                responsibility=body.responsibility,
                status="active",
                assigned_by_user_id="current-user",
            )
            created.append(assignment.to_dict())

        return {"created": created, "errors": errors}


@router.put("/organization/members/{member_id}/assignments/{assignment_id}")
async def change_responsibility(member_id: str, assignment_id: str, body: ChangeResponsibilityRequest):
    """Change the responsibility type of an assignment."""
    async with db_session() as s:
        gov_repo = GovernanceAssignmentRepository(s)
        assignment = await gov_repo.get(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        if assignment.organization_member_id != member_id:
            raise HTTPException(status_code=403, detail="Assignment does not belong to this member")
        if body.responsibility not in ("primary_owner", "monitor", "approver"):
            raise HTTPException(status_code=400, detail="Invalid responsibility type")

        # Check primary_owner conflict if changing to primary_owner
        if body.responsibility == "primary_owner":
            existing_owner = await gov_repo.get_primary_owner(assignment.project_agent_id)
            if existing_owner and existing_owner.id != assignment_id:
                raise HTTPException(
                    status_code=409,
                    detail=f"Agent already has a primary owner: {existing_owner.organization_member_id}",
                )

        updated = await gov_repo.update(assignment_id, responsibility=body.responsibility)
        return updated.to_dict()


@router.delete("/organization/members/{member_id}/assignments/{assignment_id}")
async def revoke_assignment(member_id: str, assignment_id: str):
    """Revoke a governance assignment."""
    async with db_session() as s:
        gov_repo = GovernanceAssignmentRepository(s)
        assignment = await gov_repo.get(assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        if assignment.organization_member_id != member_id:
            raise HTTPException(status_code=403, detail="Assignment does not belong to this member")
        await gov_repo.revoke(assignment_id, reason="Revoked by user")
        return {"revoked": True, "assignment_id": assignment_id}


# ── Project-centric governance endpoints ──────────────────────────────


@router.get("/projects/{project_id}/agent-governance")
async def project_governance(project_id: str):
    """Return governance coverage for all active agents in a project."""
    async with db_session() as s:
        agent_repo = AgentRepository(s)
        agents = await agent_repo.list_by_project(project_id)
        gov_repo = GovernanceAssignmentRepository(s)
        member_repo = OrganizationMemberRepository(s)

        coverage = []
        for agent in agents:
            assignments = await gov_repo.list_by_agent(agent.id)
            owners = []
            monitors = []
            approvers = []
            for a in assignments:
                member = await member_repo.get(a.organization_member_id)
                entry = {
                    "assignment_id": a.id,
                    "member_id": a.organization_member_id,
                    "member_name": member.name if member else a.organization_member_id,
                    "responsibility": a.responsibility,
                    "status": a.status,
                }
                if a.responsibility == "primary_owner":
                    owners.append(entry)
                elif a.responsibility == "monitor":
                    monitors.append(entry)
                elif a.responsibility == "approver":
                    approvers.append(entry)

            coverage.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "agent_role": agent.role,
                "agent_designation": agent.designation,
                "primary_owner": owners[0] if owners else None,
                "monitors": monitors,
                "approvers": approvers,
                "has_owner": len(owners) > 0,
                "needs_review": any(a.status == "needs_review" for a in assignments),
            })

        total = len(coverage)
        owned = sum(1 for c in coverage if c["has_owner"])
        return {
            "project_id": project_id,
            "total_agents": total,
            "owned_agents": owned,
            "unowned_agents": total - owned,
            "agents": coverage,
        }
