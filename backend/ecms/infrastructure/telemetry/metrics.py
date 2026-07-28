"""Prometheus metrics (SECTION 80/102).

Owns an isolated collector registry with standard request, latency and error metrics, plus
factories for custom collectors, and renders the Prometheus exposition format for the
``/metrics`` endpoint.
"""

from __future__ import annotations

from collections.abc import Sequence

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

__all__ = ["PROMETHEUS_CONTENT_TYPE", "MetricsRegistry"]

PROMETHEUS_CONTENT_TYPE = CONTENT_TYPE_LATEST


class MetricsRegistry:
    """Owns Prometheus collectors and renders the exposition format."""

    def __init__(self, *, namespace: str = "ecms") -> None:
        """Initialize the registry and register the standard collectors."""
        self._namespace = namespace
        self._registry = CollectorRegistry()
        self.requests_total = Counter(
            "requests_total",
            "Total number of handled requests.",
            ["method", "path", "status"],
            namespace=namespace,
            registry=self._registry,
        )
        self.request_duration_seconds = Histogram(
            "request_duration_seconds",
            "Request duration in seconds.",
            ["method", "path"],
            namespace=namespace,
            registry=self._registry,
        )
        self.errors_total = Counter(
            "errors_total",
            "Total number of errors.",
            ["component", "type"],
            namespace=namespace,
            registry=self._registry,
        )

    def observe_request(self, *, method: str, path: str, status: int, duration: float) -> None:
        """Record a completed request's status and duration."""
        self.requests_total.labels(method=method, path=path, status=str(status)).inc()
        self.request_duration_seconds.labels(method=method, path=path).observe(duration)

    def record_error(self, *, component: str, error_type: str) -> None:
        """Record an error occurrence for a component."""
        self.errors_total.labels(component=component, type=error_type).inc()

    def counter(
        self,
        name: str,
        documentation: str,
        labelnames: Sequence[str] = (),
    ) -> Counter:
        """Create and register a custom counter."""
        return Counter(
            name,
            documentation,
            list(labelnames),
            namespace=self._namespace,
            registry=self._registry,
        )

    def histogram(
        self,
        name: str,
        documentation: str,
        labelnames: Sequence[str] = (),
    ) -> Histogram:
        """Create and register a custom histogram."""
        return Histogram(
            name,
            documentation,
            list(labelnames),
            namespace=self._namespace,
            registry=self._registry,
        )

    def gauge(
        self,
        name: str,
        documentation: str,
        labelnames: Sequence[str] = (),
    ) -> Gauge:
        """Create and register a custom gauge."""
        return Gauge(
            name,
            documentation,
            list(labelnames),
            namespace=self._namespace,
            registry=self._registry,
        )

    def render(self) -> bytes:
        """Return the metrics in the Prometheus exposition format."""
        return generate_latest(self._registry)
