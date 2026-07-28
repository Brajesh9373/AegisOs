"""Tool port (SECTION 23).

Every tool implements the same lifecycle so the runtime can initialize, validate,
execute, roll back, health-check and shut down any tool uniformly.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ecms.tools.domain.tool import ToolRequest, ToolResult

__all__ = ["Tool"]


@runtime_checkable
class Tool(Protocol):
    """A replaceable, auditable external-action tool (SECTION 23).

    Operations:
        name: The tool's stable identifier.
        initialize: Prepare the tool for use.
        validate: Validate a request before execution.
        execute: Perform the requested operation.
        rollback: Undo the tool's most recent effect where possible.
        health: Report whether the tool is healthy.
        shutdown: Release the tool's resources.
    """

    @property
    def name(self) -> str: ...
    async def initialize(self) -> None: ...
    async def validate(self, request: ToolRequest) -> None: ...
    async def execute(self, request: ToolRequest) -> ToolResult: ...
    async def rollback(self) -> None: ...
    async def health(self) -> bool: ...
    async def shutdown(self) -> None: ...
