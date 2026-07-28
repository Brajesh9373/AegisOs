"""Request-context middleware (SECTION 85/102)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ecms.shared.ids import new_correlation_id, new_id

__all__ = ["RequestContextMiddleware"]

_CORRELATION_HEADER = "X-Correlation-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Binds a correlation id and request id to the ambient context per request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Bind request context and echo the correlation id on the response."""
        from ecms.shared.context import bind_context

        correlation_id = request.headers.get(_CORRELATION_HEADER) or new_correlation_id()
        bind_context(correlation_id=correlation_id, request_id=new_id("req"))
        response = await call_next(request)
        response.headers[_CORRELATION_HEADER] = correlation_id
        return response
