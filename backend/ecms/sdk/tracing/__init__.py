"""Tracing API facade."""

from ecms.infrastructure.telemetry import configure_tracing, get_tracer, traced_span

__all__ = ["configure_tracing", "get_tracer", "traced_span"]
