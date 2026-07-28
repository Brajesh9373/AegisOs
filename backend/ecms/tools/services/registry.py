"""Tool registry (SECTION 173).

Owns every available tool and supports registration, discovery and lookup. Mirrors
the plugin and connector registries.
"""

from __future__ import annotations

from ecms.shared.exceptions import NotFoundError
from ecms.tools.interfaces.tool import Tool

__all__ = ["ToolRegistry"]


class ToolRegistry:
    """Registers and resolves tools by name (SECTION 173)."""

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool under its name."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Return a registered tool by name.

        Raises:
            NotFoundError: If no tool is registered under ``name``.
        """
        tool = self._tools.get(name)
        if tool is None:
            raise NotFoundError(f"tool {name!r} is not registered")
        return tool

    def has(self, name: str) -> bool:
        """Return whether a tool is registered under ``name``."""
        return name in self._tools

    def names(self) -> list[str]:
        """Return the names of all registered tools."""
        return sorted(self._tools)
