"""Tests for the enterprise SDK."""

from __future__ import annotations

from ecms.infrastructure.telemetry import MetricsRegistry
from ecms.sdk import EcmsSDK, create_sdk


async def test_create_sdk_wires_subsystems() -> None:
    sdk = create_sdk()
    assert isinstance(sdk, EcmsSDK)
    assert sdk.settings.app_name == "ecms"
    assert sdk.container.is_registered(MetricsRegistry)
    sdk.logger("component").info("hello")
    assert sdk.tracer("component") is not None
    health = await sdk.health()
    assert health["events"] is True
    assert health["plugins"] == {}


def test_sdk_config_facade() -> None:
    from ecms.sdk.config import get_settings

    assert get_settings().app_name == "ecms"


def test_sdk_events_facade() -> None:
    from ecms.sdk.events import InMemoryEventBus

    assert InMemoryEventBus() is not None


def test_sdk_utils_facade() -> None:
    from ecms.sdk.utils import deep_merge

    assert deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_all_sub_api_facades_expose_public_api() -> None:
    from ecms.sdk import (
        auth,
        authz,
        config,
        events,
        health,
        logging,
        metrics,
        plugins,
        tracing,
        utils,
    )

    modules = (auth, authz, config, events, health, logging, metrics, plugins, tracing, utils)
    for module in modules:
        assert module.__all__
