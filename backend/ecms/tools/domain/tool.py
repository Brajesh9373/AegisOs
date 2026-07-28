"""Tool request and result models (SECTION 23/174).

A tool receives a :class:`ToolRequest` (an operation and its arguments) and
returns a :class:`ToolResult`. Results are uniform so the tool manager can audit
every invocation identically regardless of the tool.
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ecms.shared.models.base import DomainModel

__all__ = ["ToolRequest", "ToolResult"]


class ToolRequest(DomainModel):
    """A request to perform one tool operation (SECTION 174)."""

    operation: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(DomainModel):
    """The outcome of a tool operation (SECTION 174)."""

    success: bool
    output: Any = None
    error: str | None = None
    artifacts: list[str] = Field(default_factory=list)
