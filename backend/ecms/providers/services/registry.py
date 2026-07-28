"""Connector registry (SECTION 119).

Owns every registered connector and resolves them by name.
"""

from __future__ import annotations

from ecms.providers.interfaces.connector import Connector
from ecms.shared.exceptions import NotFoundError

__all__ = ["ConnectorRegistry"]


class ConnectorRegistry:
    """Registers and resolves connectors by name (SECTION 119)."""

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._connectors: dict[str, Connector] = {}

    def register(self, connector: Connector) -> None:
        """Register a connector under its name."""
        self._connectors[connector.name] = connector

    def get(self, name: str) -> Connector:
        """Return a registered connector by name.

        Raises:
            NotFoundError: If no connector is registered under ``name``.
        """
        connector = self._connectors.get(name)
        if connector is None:
            raise NotFoundError(f"connector {name!r} is not registered")
        return connector

    def has(self, name: str) -> bool:
        """Return whether a connector is registered under ``name``."""
        return name in self._connectors

    def names(self) -> list[str]:
        """Return the names of all registered connectors."""
        return sorted(self._connectors)
