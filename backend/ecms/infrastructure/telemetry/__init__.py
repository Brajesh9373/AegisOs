"""Logging, metrics and tracing bootstrap."""

from ecms.infrastructure.telemetry.log import (
    add_context,
    configure_logging,
    get_logger,
    scrub_secrets,
)
from ecms.infrastructure.telemetry.metrics import PROMETHEUS_CONTENT_TYPE, MetricsRegistry
from ecms.infrastructure.telemetry.tracing import configure_tracing, get_tracer, traced_span

__all__ = [
    "PROMETHEUS_CONTENT_TYPE",
    "MetricsRegistry",
    "add_context",
    "configure_logging",
    "configure_tracing",
    "get_logger",
    "get_tracer",
    "scrub_secrets",
    "traced_span",
]
