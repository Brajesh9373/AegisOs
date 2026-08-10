"""Agent repository — CRUD for digital org hierarchy."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.persistence.models.agent import Agent
from ecms.shared.certifications import default_certificates_for_agent


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **kwargs: Any) -> Agent:
        if not kwargs.get("certificates"):
            kwargs["certificates"] = default_certificates_for_agent(kwargs)
        agent = Agent(**kwargs)
        self._session.add(agent)
        await self._session.flush()
        return agent

    async def get(self, agent_id: str) -> Agent | None:
        stmt = select(Agent).where(Agent.id == agent_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Agent | None:
        stmt = select(Agent).where(Agent.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Agent]:
        stmt = select(Agent).order_by(Agent.department, Agent.role, Agent.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_department(self, dept: str) -> list[Agent]:
        stmt = select(Agent).where(Agent.department == dept).order_by(Agent.role, Agent.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_manager(self, manager_id: str) -> list[Agent]:
        stmt = select(Agent).where(Agent.reports_to == manager_id).order_by(Agent.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_project(self, project_id: str) -> list[Agent]:
        stmt = select(Agent).where(Agent.project_id == project_id).order_by(Agent.role, Agent.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_available(self) -> list[Agent]:
        """Active permanent agents eligible for project staffing.

        Project staffing assignments do not mutate project_id, so these agents
        stay reusable across projects.
        """
        stmt = select(Agent).where(
            Agent.project_id.is_(None),
            Agent.status == "active",
        ).order_by(Agent.department, Agent.role, Agent.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_available_tree(self) -> dict[str, Any]:
        """Return the available-agent hierarchy as a nested dict."""
        agents = await self.list_available()
        agent_map = {a.id: {**a.to_dict(), "reports": []} for a in agents}
        roots: list[dict] = []
        for a in agents:
            node = agent_map[a.id]
            if a.reports_to and a.reports_to in agent_map:
                agent_map[a.reports_to]["reports"].append(node)
            else:
                roots.append(node)
        return {"root_agents": roots, "total": len(agents)}

    async def count_available_by_designation(self) -> dict[str, int]:
        """Count available agents grouped by designation."""
        agents = await self.list_available()
        counts: dict[str, int] = {}
        for a in agents:
            d = a.designation or a.role
            counts[d] = counts.get(d, 0) + 1
        return counts

    async def assign_to_project(self, agent_id: str, project_id: str) -> Agent | None:
        """Legacy project-scoping assignment.

        New workspace staffing uses project_agent_assignments so agents remain
        reusable across projects.
        """
        agent = await self.get(agent_id)
        if not agent:
            return None
        agent.project_id = project_id
        await self._session.flush()
        return agent

    async def unassign_from_project(self, agent_id: str) -> Agent | None:
        """Legacy project_id cleanup; availability no longer depends on this."""
        agent = await self.get(agent_id)
        if not agent:
            return None
        agent.project_id = None
        await self._session.flush()
        return agent

    async def delete_by_project(self, project_id: str) -> int:
        """Delete every agent scoped to a project. Returns the count removed.

        Used to make team (re)generation idempotent — a fresh design replaces
        any prior org chart for the project.
        """
        agents = await self.list_by_project(project_id)
        count = len(agents)
        if count:
            stmt = delete(Agent).where(Agent.project_id == project_id)
            await self._session.execute(stmt)
            await self._session.flush()
        return count

    async def update(self, agent_id: str, **kwargs: Any) -> Agent | None:
        agent = await self.get(agent_id)
        if not agent:
            return None
        if "certificates" in kwargs and not kwargs["certificates"]:
            profile = {**agent.to_dict(), **kwargs}
            kwargs["certificates"] = default_certificates_for_agent(profile)
        for k, v in kwargs.items():
            if hasattr(agent, k):
                setattr(agent, k, v)
        await self._session.flush()
        return agent

    async def delete(self, agent_id: str) -> bool:
        agent = await self.get(agent_id)
        if not agent:
            return False
        # Reassign all direct reports to this agent's manager
        mgr_id = agent.reports_to
        stmt = (
            update(Agent)
            .where(Agent.reports_to == agent_id)
            .values(reports_to=mgr_id)
        )
        await self._session.execute(stmt)
        await self._session.delete(agent)
        await self._session.flush()
        return True

    async def get_org_tree(self) -> dict[str, Any]:
        """Return the full org hierarchy as a nested dict."""
        agents = await self.list_all()
        agent_map = {a.id: {**a.to_dict(), "reports": []} for a in agents}
        roots = []
        for a in agents:
            node = agent_map[a.id]
            if a.reports_to and a.reports_to in agent_map:
                agent_map[a.reports_to]["reports"].append(node)
            else:
                roots.append(node)
        return {"root_agents": roots, "total": len(agents)}

    async def find_senior_in_dept(self, dept: str) -> Agent | None:
        """Find the lowest-level agent in a department who can accept cross-team requests."""
        stmt = (
            select(Agent)
            .where(
                Agent.department == dept,
                Agent.status == "active",
                Agent.role.in_(["tech_lead", "senior_dev"]),
            )
            .order_by(Agent.role)  # senior_dev first (lower-level)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_in_reporting_chain(self, senior_id: str, junior_id: str) -> bool:
        """Check if junior reports to senior (directly or transitively)."""
        current = await self.get(junior_id)
        while current and current.reports_to:
            if current.reports_to == senior_id:
                return True
            current = await self.get(current.reports_to)
        return False
