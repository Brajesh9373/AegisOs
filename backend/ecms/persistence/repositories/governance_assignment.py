"""Governance assignment repository — links org members to project agents."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ecms.persistence.models.governance_assignment import ProjectAgentGovernanceAssignment


class GovernanceAssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **kwargs: Any) -> ProjectAgentGovernanceAssignment:
        assignment = ProjectAgentGovernanceAssignment(**kwargs)
        self._session.add(assignment)
        await self._session.flush()
        return assignment

    async def get(self, assignment_id: str) -> ProjectAgentGovernanceAssignment | None:
        stmt = select(ProjectAgentGovernanceAssignment).where(
            ProjectAgentGovernanceAssignment.id == assignment_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_member(self, member_id: str) -> list[ProjectAgentGovernanceAssignment]:
        stmt = (
            select(ProjectAgentGovernanceAssignment)
            .where(ProjectAgentGovernanceAssignment.organization_member_id == member_id)
            .order_by(ProjectAgentGovernanceAssignment.project_id, ProjectAgentGovernanceAssignment.assigned_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_project(self, project_id: str) -> list[ProjectAgentGovernanceAssignment]:
        stmt = (
            select(ProjectAgentGovernanceAssignment)
            .where(
                ProjectAgentGovernanceAssignment.project_id == project_id,
                ProjectAgentGovernanceAssignment.status == "active",
            )
            .order_by(ProjectAgentGovernanceAssignment.responsibility, ProjectAgentGovernanceAssignment.assigned_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_agent(self, agent_id: str) -> list[ProjectAgentGovernanceAssignment]:
        stmt = (
            select(ProjectAgentGovernanceAssignment)
            .where(
                ProjectAgentGovernanceAssignment.project_agent_id == agent_id,
                ProjectAgentGovernanceAssignment.status == "active",
            )
            .order_by(ProjectAgentGovernanceAssignment.responsibility)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_primary_owner(self, agent_id: str) -> ProjectAgentGovernanceAssignment | None:
        stmt = select(ProjectAgentGovernanceAssignment).where(
            ProjectAgentGovernanceAssignment.project_agent_id == agent_id,
            ProjectAgentGovernanceAssignment.responsibility == "primary_owner",
            ProjectAgentGovernanceAssignment.status == "active",
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, assignment_id: str, **kwargs: Any) -> ProjectAgentGovernanceAssignment | None:
        assignment = await self.get(assignment_id)
        if not assignment:
            return None
        for k, v in kwargs.items():
            if hasattr(assignment, k):
                setattr(assignment, k, v)
        await self._session.flush()
        return assignment

    async def revoke(self, assignment_id: str, reason: str = "") -> bool:
        assignment = await self.get(assignment_id)
        if not assignment:
            return False
        assignment.status = "revoked"
        assignment.review_reason = reason or "Revoked by user"
        await self._session.flush()
        return True

    async def mark_needs_review(self, agent_id: str, reason: str) -> int:
        """Mark all active assignments for an agent as needs_review."""
        stmt = (
            update(ProjectAgentGovernanceAssignment)
            .where(
                ProjectAgentGovernanceAssignment.project_agent_id == agent_id,
                ProjectAgentGovernanceAssignment.status == "active",
            )
            .values(status="needs_review", review_reason=reason)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount  # type: ignore[return-value]

    async def has_active_assignments(self, member_id: str) -> bool:
        stmt = select(ProjectAgentGovernanceAssignment).where(
            ProjectAgentGovernanceAssignment.organization_member_id == member_id,
            ProjectAgentGovernanceAssignment.status.in_(["active", "needs_review"]),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def delete(self, assignment_id: str) -> bool:
        assignment = await self.get(assignment_id)
        if not assignment:
            return False
        await self._session.delete(assignment)
        await self._session.flush()
        return True
