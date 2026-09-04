"""Task repository — CRUD for tasks, dependencies, and cross-team requests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.persistence.models.task import CrossTeamRequest, Task, TaskDependency


def _task_id() -> str:
    return f"task-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{hex(hash(datetime.now(UTC)) & 0xFFFF)[2:]}"


def _ctr_id() -> str:
    return f"ctr-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{hex(hash(datetime.now(UTC)) & 0xFFFF)[2:]}"


def _dep_id() -> str:
    return f"dep-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{hex(hash(datetime.now(UTC)) & 0xFFFF)[2:]}"


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Tasks ─────────────────────────────────────────────────

    async def create(
        self,
        *,
        title: str,
        assigner_id: str,
        assignee_id: str,
        description: str | None = None,
        inputs: dict[str, Any] | None = None,
        expected_output: str | None = None,
        priority: str = "normal",
    ) -> Task:
        task = Task(
            id=_task_id(),
            title=title,
            description=description,
            assigner_id=assigner_id,
            assignee_id=assignee_id,
            inputs=inputs or {},
            expected_output=expected_output,
            priority=priority,
        )
        self._session.add(task)
        await self._session.flush()
        return task

    async def get(self, task_id: str) -> Task | None:
        stmt = select(Task).where(Task.id == task_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_assignee(self, assignee_id: str, status: str | None = None) -> list[Task]:
        stmt = select(Task).where(Task.assignee_id == assignee_id)
        if status:
            stmt = stmt.where(Task.status == status)
        stmt = stmt.order_by(Task.priority, Task.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_assigner(self, assigner_id: str, status: str | None = None) -> list[Task]:
        stmt = select(Task).where(Task.assigner_id == assigner_id)
        if status:
            stmt = stmt.where(Task.status == status)
        stmt = stmt.order_by(Task.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, task_id: str, status: str, **extra: Any) -> Task | None:
        task = await self.get(task_id)
        if not task:
            return None
        task.status = status
        for k, v in extra.items():
            if hasattr(task, k):
                setattr(task, k, v)
        await self._session.flush()
        return task

    async def get_blockers(self, task_id: str) -> list[dict[str, Any]]:
        """Get all tasks blocking this task."""
        stmt = select(TaskDependency).where(TaskDependency.blocked_task_id == task_id)
        result = await self._session.execute(stmt)
        deps = result.scalars().all()
        blockers = []
        for dep in deps:
            blocker = await self.get(dep.blocker_task_id)
            if blocker:
                ctr = None
                if dep.cross_team_request_id:
                    ctr_stmt = select(CrossTeamRequest).where(
                        CrossTeamRequest.id == dep.cross_team_request_id
                    )
                    ctr_result = await self._session.execute(ctr_stmt)
                    ctr = ctr_result.scalar_one_or_none()
                blockers.append(
                    {
                        "dependency_id": dep.id,
                        "blocker_task": blocker.to_dict(),
                        "dependency_type": dep.dependency_type,
                        "cross_team_request": ctr.to_dict() if ctr else None,
                    }
                )
        return blockers

    # ── Dependencies ──────────────────────────────────────────

    async def add_dependency(
        self,
        blocked_task_id: str,
        blocker_task_id: str,
        dependency_type: str = "same_team",
        cross_team_request_id: str | None = None,
    ) -> TaskDependency:
        dep = TaskDependency(
            id=_dep_id(),
            blocked_task_id=blocked_task_id,
            blocker_task_id=blocker_task_id,
            dependency_type=dependency_type,
            cross_team_request_id=cross_team_request_id,
        )
        self._session.add(dep)
        await self._session.flush()
        return dep

    # ── Cross-Team Requests ───────────────────────────────────

    async def create_ctr(
        self,
        *,
        title: str,
        requester_id: str,
        target_dept: str,
        description: str | None = None,
        inputs: dict[str, Any] | None = None,
        priority: str = "normal",
        target_senior_id: str | None = None,
    ) -> CrossTeamRequest:
        ctr = CrossTeamRequest(
            id=_ctr_id(),
            title=title,
            description=description,
            requester_id=requester_id,
            target_dept=target_dept,
            target_senior_id=target_senior_id,
            inputs=inputs or {},
            priority=priority,
        )
        self._session.add(ctr)
        await self._session.flush()
        return ctr

    async def get_ctr(self, ctr_id: str) -> CrossTeamRequest | None:
        stmt = select(CrossTeamRequest).where(CrossTeamRequest.id == ctr_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_ctrs_by_target(
        self, target_dept: str, status: str | None = None
    ) -> list[CrossTeamRequest]:
        stmt = select(CrossTeamRequest).where(CrossTeamRequest.target_dept == target_dept)
        if status:
            stmt = stmt.where(CrossTeamRequest.status == status)
        stmt = stmt.order_by(CrossTeamRequest.priority, CrossTeamRequest.created_at.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_ctrs_by_requester(self, requester_id: str) -> list[CrossTeamRequest]:
        stmt = (
            select(CrossTeamRequest)
            .where(CrossTeamRequest.requester_id == requester_id)
            .order_by(CrossTeamRequest.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_ctr(self, ctr_id: str, **kwargs: Any) -> CrossTeamRequest | None:
        ctr = await self.get_ctr(ctr_id)
        if not ctr:
            return None
        for k, v in kwargs.items():
            if hasattr(ctr, k):
                setattr(ctr, k, v)
        await self._session.flush()
        return ctr
