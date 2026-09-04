"""Organization member repository — CRUD for permanent company hierarchy."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.persistence.models.organization_member import OrganizationMember


class OrganizationMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **kwargs: Any) -> OrganizationMember:
        member = OrganizationMember(**kwargs)
        self._session.add(member)
        await self._session.flush()
        return member

    async def get(self, member_id: str) -> OrganizationMember | None:
        stmt = select(OrganizationMember).where(OrganizationMember.id == member_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> OrganizationMember | None:
        stmt = select(OrganizationMember).where(OrganizationMember.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[OrganizationMember]:
        stmt = select(OrganizationMember).order_by(
            OrganizationMember.department,
            OrganizationMember.role,
            OrganizationMember.name,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_department(self, dept: str) -> list[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .where(OrganizationMember.department == dept)
            .order_by(OrganizationMember.role, OrganizationMember.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_manager(self, manager_id: str) -> list[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .where(OrganizationMember.reports_to == manager_id)
            .order_by(OrganizationMember.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_active(self) -> list[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .where(OrganizationMember.status == "active")
            .order_by(
                OrganizationMember.department, OrganizationMember.role, OrganizationMember.name
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, member_id: str, **kwargs: Any) -> OrganizationMember | None:
        member = await self.get(member_id)
        if not member:
            return None
        for k, v in kwargs.items():
            if hasattr(member, k):
                setattr(member, k, v)
        await self._session.flush()
        return member

    async def deactivate(self, member_id: str) -> bool:
        member = await self.get(member_id)
        if not member:
            return False
        member.status = "inactive"
        await self._session.flush()
        return True

    async def delete(self, member_id: str) -> bool:
        member = await self.get(member_id)
        if not member:
            return False
        # Reassign direct reports to this member's manager
        mgr_id = member.reports_to
        stmt = (
            update(OrganizationMember)
            .where(OrganizationMember.reports_to == member_id)
            .values(reports_to=mgr_id)
        )
        await self._session.execute(stmt)
        await self._session.delete(member)
        await self._session.flush()
        return True

    async def get_org_tree(self) -> dict[str, Any]:
        """Return the full org hierarchy as a nested dict."""
        members = await self.list_all()
        member_map = {m.id: {**m.to_dict(), "reports": []} for m in members}
        roots: list[dict] = []
        for m in members:
            node = member_map[m.id]
            if m.reports_to and m.reports_to in member_map:
                member_map[m.reports_to]["reports"].append(node)
            else:
                roots.append(node)
        return {"root_members": roots, "total": len(members)}

    async def is_in_reporting_chain(self, senior_id: str, junior_id: str) -> bool:
        """Check if junior reports to senior (directly or transitively)."""
        current = await self.get(junior_id)
        while current and current.reports_to:
            if current.reports_to == senior_id:
                return True
            current = await self.get(current.reports_to)
        return False

    async def count_by_department(self) -> dict[str, int]:
        members = await self.list_active()
        counts: dict[str, int] = {}
        for m in members:
            counts[m.department] = counts.get(m.department, 0) + 1
        return counts
