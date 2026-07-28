"""Metrics and tracing middleware (SECTION 85/102)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ecms.infrastructure.telemetry import MetricsRegistry, traced_span

__all__ = ["MetricsMiddleware", "TracingMiddleware"]


class MetricsMiddleware(BaseHTTPMiddleware):
    """Records request count and latency for every request."""

    def __init__(self, app: ASGIApp, metrics: MetricsRegistry) -> None:
        """Initialize the middleware with the metrics registry."""
        super().__init__(app)
        self._metrics = metrics

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Time the request and record its outcome."""
        start = perf_counter()
        response = await call_next(request)
        self._metrics.observe_request(
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration=perf_counter() - start,
        )
        return response


class TracingMiddleware(BaseHTTPMiddleware):
    """Wraps each request in an OpenTelemetry span."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Start a span for the request and bind its trace context."""
        with traced_span(f"{request.method} {request.url.path}"):
            return await call_next(request)
