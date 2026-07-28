"""Tool manager: the tool execution pipeline (SECTION 172/174).

Every tool invocation flows through one pipeline: permission check, validation,
execution, and event publication. Each invocation produces an auditable
:class:`ToolExecution` record and emits tool events.
"""

from __future__ import annotations

from ecms.events import EventBus
from ecms.shared.enums import ToolExecutionStatus
from ecms.shared.events import BaseEvent
from ecms.shared.ids import new_id
from ecms.shared.models import ToolExecution
from ecms.shared.time import utcnow
from ecms.tools.domain.tool import ToolRequest
from ecms.tools.events.tool_events import (
    tool_artifact_generated,
    tool_execution_completed,
    tool_execution_failed,
    tool_execution_started,
    tool_permission_denied,
)
from ecms.tools.interfaces.tool import Tool
from ecms.tools.services.governance import ToolPermissionEngine
from ecms.tools.services.registry import ToolRegistry

__all__ = ["ToolManager"]


class ToolManager:
    """Executes tools through the permission-checked, audited pipeline (SECTION 174)."""

    def __init__(
        self,
        *,
        registry: ToolRegistry | None = None,
        permissions: ToolPermissionEngine | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize with a registry, permission engine and optional event bus."""
        self._registry = registry or ToolRegistry()
        self._permissions = permissions or ToolPermissionEngine()
        self._event_bus = event_bus

    def register(self, tool: Tool) -> None:
        """Register a tool for execution."""
        self._registry.register(tool)

    async def execute(
        self,
        tool_name: str,
        request: ToolRequest,
        *,
        caller_agent: str | None = None,
        task_id: str | None = None,
        session_id: str | None = None,
        agent_permissions: list[str] | None = None,
    ) -> ToolExecution:
        """Execute a tool and return an auditable execution record (SECTION 174)."""
        if not self._permissions.check(tool_name, agent_permissions=agent_permissions):
            await self._emit(tool_permission_denied(tool_name))
            return ToolExecution(
                tool_name=tool_name,
                arguments=request.arguments,
                caller_agent=caller_agent,
                task_id=task_id,
                session_id=session_id,
                status=ToolExecutionStatus.DENIED,
            )
        tool = self._registry.get(tool_name)
        execution_id = new_id("texec")
        start = utcnow()
        await self._emit(tool_execution_started(execution_id, tool_name))
        output: object | None = None
        error: str | None = None
        artifacts: list[str] = []
        try:
            await tool.validate(request)
            result = await tool.execute(request)
            status = ToolExecutionStatus.SUCCEEDED if result.success else ToolExecutionStatus.FAILED
            output = result.output
            error = result.error
            artifacts = result.artifacts
        except Exception as exc:  # the manager records tool failures rather than raising
            status = ToolExecutionStatus.FAILED
            error = str(exc)
        end = utcnow()
        execution = ToolExecution(
            execution_id=execution_id,
            tool_name=tool_name,
            arguments=request.arguments,
            caller_agent=caller_agent,
            task_id=task_id,
            session_id=session_id,
            status=status,
            start_time=start,
            end_time=end,
            duration_ms=(end - start).total_seconds() * 1000.0,
            stdout="" if output is None else str(output),
            stderr=error or "",
            artifacts=artifacts,
        )
        await self._publish_outcome(execution)
        return execution

    async def _publish_outcome(self, execution: ToolExecution) -> None:
        if execution.status is ToolExecutionStatus.SUCCEEDED:
            await self._emit(tool_execution_completed(execution.execution_id, execution.tool_name))
            for artifact in execution.artifacts:
                await self._emit(tool_artifact_generated(execution.execution_id, artifact))
        else:
            await self._emit(
                tool_execution_failed(
                    execution.execution_id,
                    execution.tool_name,
                    execution.stderr or "unknown error",
                )
            )

    async def _emit(self, event: BaseEvent) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)
