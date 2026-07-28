"""Base tool with default lifecycle (SECTION 23).

Concrete tools extend :class:`BaseTool` and implement :meth:`execute`; the other
lifecycle methods have safe defaults that tools may override.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ecms.tools.domain.tool import ToolRequest, ToolResult

__all__ = ["BaseTool"]


class BaseTool(ABC):
    """Abstract base implementing the tool lifecycle with safe defaults (SECTION 23)."""

    name: str = "tool"

    async def initialize(self) -> None:
        """Prepare the tool for use (no-op by default)."""

    async def validate(self, request: ToolRequest) -> None:
        """Validate a request before execution (no-op by default)."""

    @abstractmethod
    async def execute(self, request: ToolRequest) -> ToolResult:
        """Perform the requested operation."""
        raise NotImplementedError

    async def rollback(self) -> None:
        """Undo the tool's most recent effect (no-op by default)."""

    async def health(self) -> bool:
        """Report whether the tool is healthy (healthy by default)."""
        return True

    async def shutdown(self) -> None:
        """Release the tool's resources (no-op by default)."""
