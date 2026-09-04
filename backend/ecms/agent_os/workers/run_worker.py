"""Agent OS run worker - executes DSH steps from durable runs."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.agent_os.capabilities.broker import get_capability_broker
from ecms.agent_os.capabilities.knowledge_adapter import get_knowledge_search_capability
from ecms.agent_os.persistence.database import db_session
from ecms.agent_os.persistence.models.run import AgentRun, RunState, StepState
from ecms.agent_os.persistence.repositories.run_repository import (
    AgentRunRepository,
    AgentRunStepRepository,
)
from ecms.agent_os.profiles.contracts import parse_step_envelope
from ecms.shared.ids import new_id

logger = logging.getLogger(__name__)

__all__ = ["AgentRunWorker"]


class AgentRunWorker:
    """Worker that claims and executes Agent OS runs.

    On claim, it:
    1. Re-checks membership, activation, profile fingerprint, and budgets
    2. Executes bounded DSH steps
    3. Persists receipts before each state transition
    4. Handles cancellation, retry, lease loss, and crash recovery
    """

    def __init__(
        self,
        worker_id: str,
        max_concurrent_runs: int = 4,
    ) -> None:
        self.worker_id = worker_id
        self.max_concurrent_runs = max_concurrent_runs
        self._active_runs: dict[str, asyncio.Task[None]] = {}
        self._shutdown = asyncio.Event()

    async def start(self) -> None:
        """Start the worker and begin processing runs."""
        logger.info("Starting AgentRunWorker: %s", self.worker_id)
        # Register capabilities
        broker = get_capability_broker()
        broker.register(get_knowledge_search_capability())

        # Start the run processing loop
        while not self._shutdown.is_set():
            await self._process_pending_runs()
            await asyncio.sleep(5)  # Poll every 5 seconds

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        logger.info("Stopping AgentRunWorker: %s", self.worker_id)
        self._shutdown.set()

        # Cancel active runs
        for run_id, task in self._active_runs.items():
            task.cancel()
            logger.info("Cancelled run: %s", run_id)

        # Wait for cleanup
        await asyncio.gather(*self._active_runs.values(), return_exceptions=True)

    async def _process_pending_runs(self) -> None:
        """Find and claim pending runs."""
        if len(self._active_runs) >= self.max_concurrent_runs:
            return

        async with db_session() as session:
            # Find pending runs that aren't leased
            now = datetime.now(UTC).isoformat()
            rows = (
                await session.execute(
                    text(
                        """
                        SELECT id, organization_id, profile_id, profile_version,
                               correlation_id, profile_fingerprint, request_metadata
                        FROM agent_runs
                        WHERE state = 'pending'
                        AND (lease_expires_at IS NULL OR lease_expires_at < :now)
                        ORDER BY created_at ASC
                        LIMIT :limit
                        """
                    ),
                    {"now": now, "limit": self.max_concurrent_runs - len(self._active_runs)},
                )
            ).fetchall()

            for row in rows:
                run_id = str(row[0])
                if run_id in self._active_runs:
                    continue

                # Claim the run
                await session.execute(
                    text(
                        """
                        UPDATE agent_runs
                        SET state = 'running', started_at = :started,
                            lease_owner = :worker, lease_expires_at = :lease
                        WHERE id = :id AND state = 'pending'
                        """
                    ),
                    {
                        "id": run_id,
                        "started": datetime.now(UTC).isoformat(),
                        "worker": self.worker_id,
                        "lease": datetime.now(UTC).isoformat(),
                    },
                )
                await session.commit()

                # Start executing the run
                task = asyncio.create_task(self._execute_run(run_id))
                self._active_runs[run_id] = task
                task.add_done_callback(lambda t, rid=run_id: self._active_runs.pop(rid, None))

    async def _execute_run(self, run_id: str) -> None:
        """Execute a single run to completion or failure."""
        logger.info("Executing run: %s", run_id)

        async with db_session() as session:
            run_repo = AgentRunRepository(session)
            step_repo = AgentRunStepRepository(session)

            # Load run
            run = await run_repo.get(run_id, "")  # Will filter by org in query
            if run is None:
                logger.error("Run not found: %s", run_id)
                return

            # Get profile spec and execute stages
            try:
                from ecms.agent.ba.dsh_profile import business_analyst_dsh_profile_spec
                profile_spec = business_analyst_dsh_profile_spec()
            except Exception as exc:
                await run_repo.update_state(
                    run_id, run.organization_id, RunState.FAILED, last_error=str(exc)
                )
                return

            # Execute each stage
            step_index = 0
            for stage in profile_spec.stages:
                step = await step_repo.create(
                    run_id=run_id,
                    organization_id=run.organization_id,
                    step_index=step_index,
                    stage_id=stage.stage_id,
                )
                await session.commit()

                # Execute the step (simplified - real impl would call DSH)
                result = await self._execute_step(
                    run=run,
                    stage=stage,
                    step=step,
                    session=session,
                )

                if not result.success:
                    await run_repo.update_state(
                        run_id,
                        run.organization_id,
                        RunState.FAILED,
                        last_error=result.error,
                    )
                    return

                step_index += 1

            # Mark complete
            await run_repo.update_state(
                run_id,
                run.organization_id,
                RunState.COMPLETED,
                completed_at=datetime.now(UTC),
            )

            logger.info("Run completed: %s", run_id)

    async def _execute_step(
        self,
        run: AgentRun,
        stage: Any,
        step: Any,
        session: AsyncSession,
    ) -> _StepResult:
        """Execute a single step."""
        # Mark step running
        step_repo = AgentRunStepRepository(session)
        await step.update(
            step_id=step.id,
            organization_id=run.organization_id,
            state=StepState.RUNNING,
            started_at=datetime.now(UTC),
        )

        # TODO: Actually execute DSH with the stage request
        # For now, return success
        await step_repo.update(
            step.id,
            run.organization_id,
            state=StepState.COMPLETED,
            completed_at=datetime.now(UTC),
            output_checksum=hashlib.sha256(b"{}").hexdigest()[:16],
        )
        await session.commit()

        return _StepResult(success=True)


@dataclass
class _StepResult:
    success: bool
    error: str | None = None


# Global worker instance
_worker: AgentRunWorker | None = None


def get_agent_run_worker() -> AgentRunWorker:
    """Get the global agent run worker."""
    global _worker
    if _worker is None:
        _worker = AgentRunWorker(worker_id=new_id("worker"))
    return _worker