"""Plugin registry with dependency-ordered lifecycle (SECTION 103)."""

from __future__ import annotations

from typing import Any

from ecms.infrastructure.di import Container
from ecms.plugins.domain.manifest import PluginState
from ecms.plugins.interfaces.plugin import Plugin
from ecms.shared.exceptions import PluginError

__all__ = ["PluginRegistry"]

_VISITING = 0
_VISITED = 1


class PluginRegistry:
    """Registers plugins and manages their dependency-ordered lifecycle (SECTION 103)."""

    def __init__(self) -> None:
        """Initialize an empty plugin registry."""
        self._plugins: dict[str, Plugin] = {}
        self._states: dict[str, PluginState] = {}

    def register(self, plugin: Plugin) -> None:
        """Validate and register a plugin.

        Raises:
            PluginError: If a plugin with the same name is already registered.
        """
        name = plugin.manifest.name
        if name in self._plugins:
            raise PluginError(f"plugin already registered: {name}")
        plugin.validate()
        self._plugins[name] = plugin
        self._states[name] = PluginState.REGISTERED

    def get(self, name: str) -> Plugin:
        """Return a registered plugin by name.

        Raises:
            PluginError: If the plugin is not registered.
        """
        plugin = self._plugins.get(name)
        if plugin is None:
            raise PluginError(f"unknown plugin: {name}")
        return plugin

    def state(self, name: str) -> PluginState:
        """Return the lifecycle state of a plugin.

        Raises:
            PluginError: If the plugin is not registered.
        """
        state = self._states.get(name)
        if state is None:
            raise PluginError(f"unknown plugin: {name}")
        return state

    def resolve_order(self) -> list[str]:
        """Return plugin names in dependency order (dependencies first).

        Raises:
            PluginError: If a dependency is missing or a cycle is detected.
        """
        order: list[str] = []
        marks: dict[str, int] = {}

        def visit(name: str) -> None:
            mark = marks.get(name)
            if mark == _VISITED:
                return
            if mark == _VISITING:
                raise PluginError(f"circular plugin dependency at {name}")
            plugin = self._plugins.get(name)
            if plugin is None:
                raise PluginError(f"missing plugin dependency: {name}")
            marks[name] = _VISITING
            for dependency in plugin.manifest.dependencies:
                visit(dependency)
            marks[name] = _VISITED
            order.append(name)

        for name in self._plugins:
            visit(name)
        return order

    def register_services(self, container: Container) -> None:
        """Register every plugin's services into the container in dependency order."""
        for name in self.resolve_order():
            self._plugins[name].register(container)

    async def initialize_all(self, context: dict[str, Any]) -> None:
        """Initialize all plugins in dependency order."""
        for name in self.resolve_order():
            await self._plugins[name].initialize(context)
            self._states[name] = PluginState.INITIALIZED

    async def start_all(self) -> None:
        """Start all plugins in dependency order."""
        for name in self.resolve_order():
            await self._plugins[name].start()
            self._states[name] = PluginState.STARTED

    async def stop_all(self) -> None:
        """Stop all plugins in reverse dependency order."""
        for name in reversed(self.resolve_order()):
            await self._plugins[name].stop()
            self._states[name] = PluginState.STOPPED

    async def shutdown_all(self) -> None:
        """Shut down all plugins in reverse dependency order."""
        for name in reversed(self.resolve_order()):
            await self._plugins[name].shutdown()

    async def reload(self, name: str) -> None:
        """Hot-reload a single plugin by name."""
        await self.get(name).reload()

    async def health(self) -> dict[str, bool]:
        """Return the health of every registered plugin."""
        return {name: await plugin.health() for name, plugin in self._plugins.items()}

    def capabilities(self) -> dict[str, list[str]]:
        """Return a mapping of capability to the plugins that provide it."""
        result: dict[str, list[str]] = {}
        for name, plugin in self._plugins.items():
            for capability in plugin.manifest.capabilities:
                result.setdefault(capability, []).append(name)
        return result
