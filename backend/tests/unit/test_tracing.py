"""Tests for distributed tracing."""

from __future__ import annotations

from opentelemetry.sdk.trace import TracerProvider

from ecms.infrastructure.telemetry import configure_tracing, get_tracer, traced_span
from ecms.shared.context import clear_context, current_context


def test_configure_returns_provider() -> None:
    provider = configure_tracing(service_name="test", set_global=False)
    assert isinstance(provider, TracerProvider)


def test_configure_console_exporter() -> None:
    provider = configure_tracing(service_name="test", console=True, set_global=False)
    assert isinstance(provider, TracerProvider)


def test_configure_sets_global_provider() -> None:
    assert configure_tracing(service_name="global-test") is not None


def test_get_tracer_returns_tracer() -> None:
    assert get_tracer("svc") is not None


def test_traced_span_binds_trace_context() -> None:
    provider = configure_tracing(service_name="test", set_global=False)
    tracer = provider.get_tracer("test")
    clear_context()
    with traced_span("op", tracer=tracer):
        context = current_context()
        assert context.trace_id is not None
        assert context.trace_id != "0" * 32
        assert context.span_id is not None
    clear_context()


def test_traced_span_default_tracer_runs() -> None:
    clear_context()
    with traced_span("op"):
        pass
    clear_context()
