"""Tests for the plugin framework."""

from __future__ import annotations

import pytest

from ecms.infrastructure import Container
from ecms.plugins import (
    BasePlugin,
    PluginManifest,
    PluginRegistry,
    PluginState,
    load_plugin,
)
from ecms.shared.exceptions import PluginError


class _SamplePlugin(BasePlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(name="sample", version="1.0.0", capabilities=["demo"])


class _DependentPlugin(BasePlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="dependent",
            version="1.0.0",
            dependencies=["sample"],
            capabilities=["demo"],
        )


class _CyclicA(BasePlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(name="a", version="1.0.0", dependencies=["b"])


class _CyclicB(BasePlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(name="b", version="1.0.0", dependencies=["a"])


async def test_register_and_lifecycle() -> None:
    registry = PluginRegistry()
    registry.register(_SamplePlugin())
    assert registry.state("sample") is PluginState.REGISTERED
    await registry.initialize_all({})
    assert registry.state("sample") is PluginState.INITIALIZED
    await registry.start_all()
    assert registry.state("sample") is PluginState.STARTED
    assert await registry.health() == {"sample": True}
    await registry.reload("sample")
    await registry.stop_all()
    assert registry.state("sample") is PluginState.STOPPED
    await registry.shutdown_all()


def test_duplicate_registration_raises() -> None:
    registry = PluginRegistry()
    registry.register(_SamplePlugin())
    with pytest.raises(PluginError):
        registry.register(_SamplePlugin())


def test_dependency_ordering() -> None:
    registry = PluginRegistry()
    registry.register(_DependentPlugin())
    registry.register(_SamplePlugin())
    assert registry.resolve_order() == ["sample", "dependent"]


def test_missing_dependency_raises() -> None:
    registry = PluginRegistry()
    registry.register(_DependentPlugin())
    with pytest.raises(PluginError):
        registry.resolve_order()


def test_circular_dependency_raises() -> None:
    registry = PluginRegistry()
    registry.register(_CyclicA())
    registry.register(_CyclicB())
    with pytest.raises(PluginError):
        registry.resolve_order()


def test_capability_discovery() -> None:
    registry = PluginRegistry()
    registry.register(_SamplePlugin())
    registry.register(_DependentPlugin())
    assert set(registry.capabilities()["demo"]) == {"sample", "dependent"}


def test_get_and_state_unknown_raise() -> None:
    registry = PluginRegistry()
    with pytest.raises(PluginError):
        registry.get("nope")
    with pytest.raises(PluginError):
        registry.state("nope")


def test_configure_and_register_services() -> None:
    registry = PluginRegistry()
    plugin = _SamplePlugin()
    registry.register(plugin)
    plugin.configure({"key": "value"})
    registry.register_services(Container())


def test_load_plugin_invalid_path() -> None:
    with pytest.raises(PluginError):
        load_plugin("no-colon")


def test_load_plugin_missing_module() -> None:
    with pytest.raises(PluginError):
        load_plugin("nonexistent_module_xyz:Thing")


def test_load_plugin_success() -> None:
    plugin = load_plugin("ecms.plugins.tests.test_registry:_SamplePlugin")
    assert plugin.manifest.name == "sample"
