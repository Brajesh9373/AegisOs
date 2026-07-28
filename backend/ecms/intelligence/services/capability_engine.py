"""Capability engine (SECTION 289).

Discovers the capabilities available to the planner - tools and connectors - so
planning always uses discovered capabilities instead of hardcoded implementations.
"""

from __future__ import annotations

from ecms.providers.services.registry import ConnectorRegistry
from ecms.tools.services.registry import ToolRegistry

__all__ = ["CapabilityEngine"]


class CapabilityEngine:
    """Discovers available platform capabilities for planning (SECTION 289)."""

    def __init__(
        self,
        *,
        tools: ToolRegistry | None = None,
        connectors: ConnectorRegistry | None = None,
    ) -> None:
        """Initialize with optional tool and connector registries."""
        self._tools = tools
        self._connectors = connectors

    def discover(self) -> dict[str, list[str]]:
        """Return the names of available tools and connectors."""
        return {
            "tools": self._tools.names() if self._tools is not None else [],
            "connectors": (self._connectors.names() if self._connectors is not None else []),
        }
