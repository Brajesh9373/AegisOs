"""The real DSH implementation of the Business Analyst stage-executor port."""

from __future__ import annotations

from ecms.agent.ba.cognition.contracts import (
    BAExecutionResponse,
    BAStageExecutor,
    BAStageInvocation,
)
from ecms.agent.dsh_runtime import DSHExecutionError, DSHRuntime

__all__ = ["DSHBAStageExecutor"]


class DSHBAStageExecutor(BAStageExecutor):
    """Execute only host-rendered BA invocations through the pinned DSH profile."""

    def __init__(self, runtime: DSHRuntime) -> None:
        """Initialize with an already-configured real business-analyst runtime."""
        if runtime.profile != "business-analyst":
            raise ValueError("DSH BA executor requires the business-analyst DSH profile")
        self._runtime = runtime

    async def execute(self, invocation: BAStageInvocation) -> BAExecutionResponse:
        """Send the opaque rendered prompt to DSH without passing cognition access."""
        result = await self._runtime.run_agent_task(
            invocation.rendered_prompt,
            metadata={
                "context_snapshot": invocation.packet.snapshot_hash,
                "stage": invocation.stage.value,
                "attempt": str(invocation.attempt),
            },
        )
        if not result.output:
            raise DSHExecutionError("DSH business-analyst executor returned an empty response")
        return BAExecutionResponse(
            output=result.output,
            duration_seconds=result.duration_seconds,
            runtime_metadata=result.metadata,
        )
