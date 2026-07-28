"""Base plugin providing no-op lifecycle defaults (SECTION 61)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ecms.infrastructure.di import Container
from ecms.plugins.domain.manifest import PluginManifest

__all__ = ["BasePlugin"]


class BasePlugin(ABC):
    """Base class implementing no-op lifecycle defaults; subclasses override as needed."""

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest:
        """Return the plugin's declared manifest."""

    def validate(self) -> None:
        """Validate the plugin. Override to add checks."""

    def register(self, container: Container) -> None:
        """Register the plugin's services into the container. Override to add registrations."""

    def configure(self, config: dict[str, Any]) -> None:
        """Apply configuration to the plugin. Override to consume config."""

    async def initialize(self, context: dict[str, Any]) -> None:
        """Initialize the plugin. Override to set up resources."""

    async def start(self) -> None:
        """Start the plugin. Override to begin work."""

    async def stop(self) -> None:
        """Stop the plugin. Override to pause work."""

    async def reload(self) -> None:
        """Reload the plugin. Override to hot-reload."""

    async def health(self) -> bool:
        """Return whether the plugin is healthy."""
        return True

    async def shutdown(self) -> None:
        """Release the plugin's resources. Override to clean up."""
