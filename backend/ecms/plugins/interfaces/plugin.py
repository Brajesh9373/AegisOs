"""Plugin port (SECTION 61)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ecms.infrastructure.di import Container
from ecms.plugins.domain.manifest import PluginManifest

__all__ = ["Plugin"]


@runtime_checkable
class Plugin(Protocol):
    """A pluggable extension with a declared manifest and lifecycle (SECTION 61).

    Operations:
        manifest: The plugin's declared metadata.
        validate: Validate the plugin's configuration and dependencies.
        register: Register the plugin's services into the container.
        configure: Apply configuration to the plugin.
        initialize: Initialize the plugin with a shared context.
        start: Start the plugin.
        stop: Stop the plugin.
        reload: Reload the plugin (hot reload).
        health: Return whether the plugin is healthy.
        shutdown: Release the plugin's resources.
    """

    @property
    def manifest(self) -> PluginManifest: ...
    def validate(self) -> None: ...
    def register(self, container: Container) -> None: ...
    def configure(self, config: dict[str, Any]) -> None: ...
    async def initialize(self, context: dict[str, Any]) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def reload(self) -> None: ...
    async def health(self) -> bool: ...
    async def shutdown(self) -> None: ...
