"""Agent OS run repositories for tenant-scoped persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.agent_os.persistence.models.run import AgentRun, AgentRunStep, RunState, StepState
from ecms.shared.ids import new_id

__all__ = ["AgentRunRepository", "AgentRunStepRepository"]


class AgentRunRepository:
    """Repository for AgentRun persistence with tenant isolation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        organization_id: str,
        profile_id: str,
        profile_version: str,
        correlation_id: str,
        idempotency_key: str,
        profile_fingerprint: str,
        request_metadata: dict[str, Any] | None = None,
    ) -> AgentRun:
        """Create a new AgentRun with the given organization scope."""
        run = AgentRun(
            id=new_id("run"),
            organization_id=organization_id,
            profile_id=profile_id,
            profile_version=profile_version,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            profile_fingerprint=profile_fingerprint,
            request_metadata=request_metadata or {},
            state=RunState.PENDING.value,
        )
        self._session.add(run)
        return run

    async def get(self, run_id: str, organization_id: str) -> AgentRun | None:
        """Get a run by ID within organization scope."""
        stmt = select(AgentRun).where(
            AgentRun.id == run_id,
            AgentRun.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_correlation(
        self, correlation_id: str, organization_id: str
    ) -> AgentRun | None:
        """Get a run by correlation ID within organization scope."""
        stmt = select(AgentRun).where(
            AgentRun.correlation_id == correlation_id,
            AgentRun.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_org(
        self,
        organization_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        state: RunState | None = None,
    ) -> Sequence[AgentRun]:
        """List runs within organization scope."""
        stmt = (
            select(AgentRun)
            .where(AgentRun.organization_id == organization_id)
            .order_by(AgentRun.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if state is not None:
            stmt = stmt.where(AgentRun.state == state.value)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update_state(
        self,
        run_id: str,
        organization_id: str,
        state: RunState,
        *,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        execution_duration_ms: int | None = None,
        total_steps: int | None = None,
        last_error: str | None = None,
    ) -> bool:
        """Update run state with timing metrics. Returns True if updated."""
        updates: dict[str, Any] = {"state": state.value}
        if started_at is not None:
            updates["started_at"] = started_at
        if completed_at is not None:
            updates["completed_at"] = completed_at
        if execution_duration_ms is not None:
            updates["execution_duration_ms"] = execution_duration_ms
        if total_steps is not None:
            updates["total_steps"] = total_steps
        if last_error is not None:
            updates["last_error"] = last_error

        stmt = (
            update(AgentRun)
            .where(
                AgentRun.id == run_id,
                AgentRun.organization_id == organization_id,
            )
            .values(**updates)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0


class AgentRunStepRepository:
    """Repository for AgentRunStep persistence with tenant isolation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        run_id: str,
        organization_id: str,
        step_index: int,
        stage_id: str,
    ) -> AgentRunStep:
        """Create a new step within an existing run."""
        step = AgentRunStep(
            id=new_id("stp"),
            run_id=run_id,
            organization_id=organization_id,
            step_index=step_index,
            stage_id=stage_id,
            state=StepState.PENDING.value,
            receipt_json={},
            output_checksum="",
        )
        self._session.add(step)
        return step

    async def get(self, step_id: str, organization_id: str) -> AgentRunStep | None:
        """Get a step by ID within organization scope."""
        stmt = select(AgentRunStep).where(
            AgentRunStep.id == step_id,
            AgentRunStep.organization_id == organization_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_run(
        self, run_id: str, organization_id: str
    ) -> Sequence[AgentRunStep]:
        """Get all steps for a run, ordered by step_index."""
        stmt = (
            select(AgentRunStep)
            .where(
                AgentRunStep.run_id == run_id,
                AgentRunStep.organization_id == organization_id,
            )
            .order_by(AgentRunStep.step_index)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_latest_step(
        self, run_id: str, organization_id: str
    ) -> AgentRunStep | None:
        """Get the most recent step for a run."""
        stmt = (
            select(AgentRunStep)
            .where(
                AgentRunStep.run_id == run_id,
                AgentRunStep.organization_id == organization_id,
            )
            .order_by(AgentRunStep.step_index.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        step_id: str,
        organization_id: str,
        *,
        state: StepState | None = None,
        receipt_json: dict[str, Any] | None = None,
        output_checksum: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        execution_duration_ms: int | None = None,
        repair_attempts: int | None = None,
        last_error: str | None = None,
    ) -> bool:
        """Update step state and metrics. Returns True if updated."""
        updates: dict[str, Any] = {}
        if state is not None:
            updates["state"] = state.value
        if receipt_json is not None:
            updates["receipt_json"] = receipt_json
        if output_checksum is not None:
            updates["output_checksum"] = output_checksum
        if started_at is not None:
            updates["started_at"] = started_at
        if completed_at is not None:
            updates["completed_at"] = completed_at
        if execution_duration_ms is not None:
            updates["execution_duration_ms"] = execution_duration_ms
        if repair_attempts is not None:
            updates["repair_attempts"] = repair_attempts
        if last_error is not None:
            updates["last_error"] = last_error

        if not updates:
            return False

        stmt = (
            update(AgentRunStep)
            .where(
                AgentRunStep.id == step_id,
                AgentRunStep.organization_id == organization_id,
            )
            .values(**updates)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0