"""Enterprise SDK facade (SECTION 104).

Provides a single, fully-wired entry point (:class:`EcmsSDK`) exposing every foundation
subsystem: configuration, logging, events, plugins, authentication, authorization, metrics,
tracing and health.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog
from opentelemetry.trace import Tracer

from ecms.auth import JwtAuthenticationService, JwtTokenCodec, PolicyAuthorizationService
from ecms.auth.interfaces.authorization import AuthorizationService
from ecms.auth.interfaces.service import AuthenticationService
from ecms.configuration import AppSettings, Profile, get_settings
from ecms.events import EventBus, InMemoryEventBus
from ecms.infrastructure import Container
from ecms.infrastructure.telemetry import (
    MetricsRegistry,
    configure_logging,
    get_logger,
    get_tracer,
)
from ecms.plugins import PluginRegistry

__all__ = ["EcmsSDK", "create_sdk"]


@dataclass(frozen=True)
class EcmsSDK:
    """Unified, read-only entry point exposing the foundation subsystems (SECTION 104)."""

    settings: AppSettings
    container: Container
    events: EventBus
    plugins: PluginRegistry
    authentication: AuthenticationService
    authorization: AuthorizationService
    metrics: MetricsRegistry

    def logger(self, name: str) -> structlog.typing.FilteringBoundLogger:
        """Return a structured logger for a component (Logging API)."""
        return get_logger(name)

    def tracer(self, name: str) -> Tracer:
        """Return a tracer for a component (Tracing API)."""
        return get_tracer(name)

    async def health(self) -> dict[str, Any]:
        """Return aggregated health of the event bus and plugins (Health API)."""
        return {
            "events": await self.events.health(),
            "plugins": await self.plugins.health(),
        }


def create_sdk(settings: AppSettings | None = None) -> EcmsSDK:
    """Build a fully-wired SDK with default foundation services (SECTION 104)."""
    resolved = settings or get_settings()
    configure_logging(
        level=resolved.log_level,
        json_logs=resolved.environment is not Profile.DEVELOPMENT,
    )
    container = Container()
    events: EventBus = InMemoryEventBus()
    plugins = PluginRegistry()
    authentication: AuthenticationService = JwtAuthenticationService(JwtTokenCodec())
    authorization: AuthorizationService = PolicyAuthorizationService()
    metrics = MetricsRegistry()
    container.register_value(Container, container)
    container.register_value(MetricsRegistry, metrics)
    container.register_value(PluginRegistry, plugins)
    return EcmsSDK(
        settings=resolved,
        container=container,
        events=events,
        plugins=plugins,
        authentication=authentication,
        authorization=authorization,
        metrics=metrics,
    )
