"""Repository for project agent positions and reusable workforce assignments."""

from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.persistence.models.agent import Agent
from ecms.persistence.models.organization_member import OrganizationMember
from ecms.persistence.models.project_agent_position import (
    ProjectAgentAssignment,
    ProjectAgentPosition,
    ProjectHumanAssignment,
)


def normalize_designation(value: str | None) -> str:
    """Normalize titles for deterministic matching across BA and admin input."""
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


class ProjectAgentPositionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_project_positions(
        self, project_id: str, rows: list[dict[str, Any]]
    ) -> list[ProjectAgentPosition]:
        """Replace the BA-designed project positions and cascade old assignments."""
        await self._session.execute(
            delete(ProjectAgentPosition).where(ProjectAgentPosition.project_id == project_id)
        )
        await self._session.flush()

        positions: list[ProjectAgentPosition] = []
        for row in rows:
            position_key = row["id"].split(":", 1)[-1] if ":" in row["id"] else row["id"]
            position = ProjectAgentPosition(
                id=row["id"],
                project_id=project_id,
                position_key=position_key,
                name=row.get("name")
                or row.get("designation")
                or row.get("role")
                or "Agent Position",
                role=row.get("role") or "",
                designation=row.get("designation") or row.get("role") or "",
                role_description=row.get("role_description"),
                skills=row.get("skills") or [],
                department=row.get("department") or "delivery",
                reports_to=row.get("reports_to"),
                model=row.get("model"),
                tool_policy=row.get("tool_policy") or {},
                system_prompt_addon=row.get("system_prompt_addon"),
                automation=row.get("automation") or {},
                features=row.get("features") or {},
                status=row.get("status") or "active",
            )
            self._session.add(position)
            positions.append(position)

        await self._session.flush()
        return positions

    async def get(self, position_id: str) -> ProjectAgentPosition | None:
        result = await self._session.execute(
            select(ProjectAgentPosition).where(ProjectAgentPosition.id == position_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: str) -> list[ProjectAgentPosition]:
        result = await self._session.execute(
            select(ProjectAgentPosition)
            .where(ProjectAgentPosition.project_id == project_id)
            .order_by(
                ProjectAgentPosition.department,
                ProjectAgentPosition.role,
                ProjectAgentPosition.name,
            )
        )
        return list(result.scalars().all())

    async def list_assignments_by_project(self, project_id: str) -> dict[str, Agent]:
        result = await self._session.execute(
            select(ProjectAgentAssignment.position_id, Agent)
            .join(
                ProjectAgentPosition, ProjectAgentPosition.id == ProjectAgentAssignment.position_id
            )
            .join(Agent, Agent.id == ProjectAgentAssignment.agent_id)
            .where(ProjectAgentPosition.project_id == project_id)
        )
        return {position_id: agent for position_id, agent in result.all()}

    async def serialize_project(self, project_id: str) -> list[dict[str, Any]]:
        positions = await self.list_by_project(project_id)
        assignments = await self.list_assignments_by_project(project_id)
        return [position.to_dict(assignments.get(position.id)) for position in positions]

    async def assign(
        self, position_id: str, agent_id: str, assigned_by_user_id: str | None = None
    ) -> ProjectAgentAssignment | None:
        position = await self.get(position_id)
        if not position:
            return None

        agent_result = await self._session.execute(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.status == "active",
                Agent.project_id.is_(None),
            )
        )
        agent = agent_result.scalar_one_or_none()
        if not agent:
            return None

        existing = await self._session.get(ProjectAgentAssignment, position_id)
        if existing:
            existing.agent_id = agent_id
            existing.assigned_by_user_id = assigned_by_user_id
            await self._session.flush()
            return existing

        assignment = ProjectAgentAssignment(
            position_id=position_id,
            agent_id=agent_id,
            assigned_by_user_id=assigned_by_user_id,
        )
        self._session.add(assignment)
        await self._session.flush()
        return assignment

    async def auto_assign_project(self, project_id: str) -> int:
        """Fill project positions from active permanent agents by designation.

        Agents are reusable across projects. Within one project, prefer distinct
        agents so the hierarchy does not show the same worker twice.
        """
        positions = await self.list_by_project(project_id)
        agent_result = await self._session.execute(
            select(Agent)
            .where(Agent.status == "active", Agent.project_id.is_(None))
            .order_by(Agent.department, Agent.role, Agent.name, Agent.id)
        )
        agents = list(agent_result.scalars().all())
        used_in_project: set[str] = set()
        assigned = 0

        for position in positions:
            desired = normalize_designation(position.designation or position.role)
            candidates = [
                agent
                for agent in agents
                if normalize_designation(agent.designation or agent.role) == desired
            ]
            if not candidates:
                candidates = [
                    agent
                    for agent in agents
                    if normalize_designation(agent.role) == normalize_designation(position.role)
                ]
            agent = next(
                (candidate for candidate in candidates if candidate.id not in used_in_project), None
            )
            if not agent:
                continue
            await self.assign(position.id, agent.id, assigned_by_user_id="ba_agent")
            used_in_project.add(agent.id)
            assigned += 1

        return assigned

    async def list_active_organization_members(self) -> list[OrganizationMember]:
        result = await self._session.execute(
            select(OrganizationMember)
            .where(OrganizationMember.status == "active")
            .order_by(OrganizationMember.reports_to.nullsfirst(), OrganizationMember.name)
        )
        return list(result.scalars().all())

    def _select_workspace_owner(
        self, members: list[OrganizationMember]
    ) -> OrganizationMember | None:
        if not members:
            return None

        roots = [member for member in members if not member.reports_to]

        def norm(value: str | None) -> str:
            return (value or "").lower().replace("_", " ").replace("-", " ").strip()

        for member in roots:
            role = norm(member.role)
            designation = norm(member.designation)
            if (
                role in {"ceo", "chief executive officer"}
                or "chief executive officer" in designation
            ):
                return member
        return roots[0] if roots else members[0]

    async def ensure_workspace_owner(
        self,
        project_id: str,
        *,
        assigned_by_user_id: str | None = "ba_agent",
        source: str = "team_design",
    ) -> ProjectHumanAssignment | None:
        members = await self.list_active_organization_members()
        owner = self._select_workspace_owner(members)
        if not owner:
            return None

        result = await self._session.execute(
            select(ProjectHumanAssignment).where(
                ProjectHumanAssignment.project_id == project_id,
                ProjectHumanAssignment.scope == "workspace_owner",
                ProjectHumanAssignment.status == "active",
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.organization_member_id = owner.id
            existing.responsibility = "workspace_owner"
            existing.assigned_by_user_id = assigned_by_user_id
            existing.source = source
            await self._session.flush()
            return existing

        assignment = ProjectHumanAssignment(
            id=f"human-{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            organization_member_id=owner.id,
            position_id=None,
            scope="workspace_owner",
            responsibility="workspace_owner",
            assigned_by_user_id=assigned_by_user_id,
            source=source,
            status="active",
        )
        self._session.add(assignment)
        await self._session.flush()
        return assignment

    def _score_position_owner(
        self,
        position: ProjectAgentPosition,
        member: OrganizationMember,
        workspace_owner_id: str | None,
    ) -> float:
        if member.id == workspace_owner_id:
            return -1.0

        position_department = normalize_designation(position.department)
        member_department = normalize_designation(member.department)
        position_role = normalize_designation(position.role)
        position_designation = normalize_designation(position.designation)
        member_role = normalize_designation(member.role)
        member_designation = normalize_designation(member.designation)
        position_skills = {
            normalize_designation(skill) for skill in (position.skills or []) if skill
        }
        member_skills = {normalize_designation(skill) for skill in (member.skills or []) if skill}

        score = 0.0
        if position_department and member_department:
            if position_department == member_department:
                score += 0.45
            elif (
                position_department in member_department or member_department in position_department
            ):
                score += 0.25

        department_aliases = {
            "architecture": {"engineering", "leadership", "platform"},
            "analysis": {"product", "delivery operations", "leadership"},
            "delivery": {"delivery operations", "customer success", "leadership"},
            "sre": {"devops", "platform", "engineering"},
            "infrastructure": {"devops", "platform", "engineering"},
            "integration": {"backend", "platform", "engineering"},
            "security": {"security", "leadership"},
            "data": {"data", "engineering"},
            "qa": {"qa", "engineering"},
            "frontend": {"frontend", "engineering"},
            "backend": {"backend", "engineering"},
        }
        for key, aliases in department_aliases.items():
            if key in position_department and member_department in aliases:
                score += 0.35

        position_words = set(f"{position_role} {position_designation}".split())
        member_words = set(f"{member_role} {member_designation}".split())
        role_overlap = position_words & member_words - {"and", "of", "the", "agent", "engineer"}
        if role_overlap:
            score += 0.25 * min(1.0, len(role_overlap) / max(len(position_words), 1))

        text = f"{position_department} {position_role} {position_designation}"
        member_text = f"{member_department} {member_role} {member_designation}"
        targeted_terms = [
            (
                ("sre", "infrastructure", "reliability", "devops"),
                ("devops", "platform", "infrastructure", "reliability"),
            ),
            (("integration", "connector", "api"), ("backend", "platform", "integration", "api")),
            (
                ("solution", "architect", "architecture"),
                ("cto", "director engineering", "architecture", "engineering"),
            ),
            (
                ("business analyst", "requirements", "analysis"),
                ("product", "program", "delivery", "cpo"),
            ),
            (("delivery", "engagement"), ("program", "delivery", "operations", "coo")),
            (("security", "compliance"), ("security", "cto", "compliance")),
            (("quality", "qa", "acceptance"), ("qa", "quality", "test")),
        ]
        for position_terms, member_terms in targeted_terms:
            if any(term in text for term in position_terms) and any(
                term in member_text for term in member_terms
            ):
                score += 0.4

        if position_skills and member_skills:
            skill_overlap = position_skills & member_skills
            if skill_overlap:
                score += 0.2 * min(1.0, len(skill_overlap) / max(len(position_skills), 1))

        member_title = f"{member_role} {member_designation}"
        if any(
            term in member_title
            for term in ("manager", "lead", "director", "head", "cto", "cpo", "coo", "cfo")
        ):
            score += 0.1

        return score

    async def ensure_position_owners(
        self,
        project_id: str,
        *,
        assigned_by_user_id: str | None = "ba_agent",
        source: str = "team_design",
    ) -> int:
        positions = await self.list_by_project(project_id)
        members = await self.list_active_organization_members()
        if not positions or not members:
            return 0

        workspace_owner = await self.ensure_workspace_owner(
            project_id,
            assigned_by_user_id=assigned_by_user_id,
            source=source,
        )
        workspace_owner_id = workspace_owner.organization_member_id if workspace_owner else None

        existing_result = await self._session.execute(
            select(ProjectHumanAssignment).where(
                ProjectHumanAssignment.project_id == project_id,
                ProjectHumanAssignment.scope == "position_owner",
                ProjectHumanAssignment.status == "active",
            )
        )
        existing_by_position = {
            assignment.position_id: assignment
            for assignment in existing_result.scalars().all()
            if assignment.position_id
        }

        used_member_ids: set[str] = set()
        persisted = 0
        for position in positions:
            best_member = max(
                members,
                key=lambda member: self._score_position_owner(position, member, workspace_owner_id),
            )
            best_score = self._score_position_owner(position, best_member, workspace_owner_id)
            if best_score < 0:
                best_member = self._select_workspace_owner(members) or members[0]

            # Prefer distinct human owners when there is another reasonable candidate.
            if best_member.id in used_member_ids:
                alternatives = sorted(
                    members,
                    key=lambda member: self._score_position_owner(
                        position, member, workspace_owner_id
                    ),
                    reverse=True,
                )
                alternative = next(
                    (
                        member
                        for member in alternatives
                        if member.id not in used_member_ids
                        and self._score_position_owner(position, member, workspace_owner_id)
                        >= max(0.15, best_score * 0.65)
                    ),
                    None,
                )
                if alternative:
                    best_member = alternative

            used_member_ids.add(best_member.id)
            existing = existing_by_position.get(position.id)
            if existing:
                existing.organization_member_id = best_member.id
                existing.responsibility = "primary_owner"
                existing.assigned_by_user_id = assigned_by_user_id
                existing.source = source
                persisted += 1
                continue

            assignment = ProjectHumanAssignment(
                id=f"human-{uuid.uuid4().hex[:12]}",
                project_id=project_id,
                organization_member_id=best_member.id,
                position_id=position.id,
                scope="position_owner",
                responsibility="primary_owner",
                assigned_by_user_id=assigned_by_user_id,
                source=source,
                status="active",
            )
            self._session.add(assignment)
            persisted += 1

        await self._session.flush()
        return persisted

    async def serialize_human_assignments(self, project_id: str) -> list[dict[str, Any]]:
        result = await self._session.execute(
            select(ProjectHumanAssignment, OrganizationMember)
            .join(
                OrganizationMember,
                OrganizationMember.id == ProjectHumanAssignment.organization_member_id,
            )
            .where(
                ProjectHumanAssignment.project_id == project_id,
                ProjectHumanAssignment.status == "active",
            )
            .order_by(ProjectHumanAssignment.scope, OrganizationMember.name)
        )
        return [assignment.to_dict(member) for assignment, member in result.all()]
