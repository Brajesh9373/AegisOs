"""Distributed tracing (SECTION 85/102).

Configures an OpenTelemetry tracer provider and provides a ``traced_span`` context manager
that binds the active OTel trace and span ids into the ECMS request context so that logs
and events emitted within the span carry the same trace correlation.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import Span, Tracer

from ecms.shared.context import bind_context

__all__ = ["configure_tracing", "get_tracer", "traced_span"]

_TRACE_ID_HEX = 32
_SPAN_ID_HEX = 16


def configure_tracing(
    *,
    service_name: str = "ecms",
    console: bool = False,
    set_global: bool = True,
) -> TracerProvider:
    """Create and optionally install an OpenTelemetry tracer provider (SECTION 85).

    Args:
        service_name: The ``service.name`` resource attribute.
        console: When true, export spans to the console.
        set_global: When true, install the provider as the global tracer provider.

    Returns:
        The configured tracer provider.
    """
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    if console:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    if set_global:
        trace.set_tracer_provider(provider)
    return provider


def get_tracer(name: str) -> Tracer:
    """Return a tracer from the global tracer provider."""
    return trace.get_tracer(name)


@contextmanager
def traced_span(name: str, tracer: Tracer | None = None) -> Iterator[Span]:
    """Start a span and bind its trace/span ids into the ECMS request context."""
    active_tracer = tracer if tracer is not None else trace.get_tracer("ecms")
    with active_tracer.start_as_current_span(name) as span:
        span_context = span.get_span_context()
        bind_context(
            trace_id=format(span_context.trace_id, f"0{_TRACE_ID_HEX}x"),
            span_id=format(span_context.span_id, f"0{_SPAN_ID_HEX}x"),
        )
        yield span
