"""Rate-limiting middleware (SECTION 82/105)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from time import monotonic

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

__all__ = ["RateLimitMiddleware"]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window, per-client rate limiter."""

    def __init__(self, app: ASGIApp, *, limit: int = 1000, window_seconds: float = 60.0) -> None:
        """Initialize the limiter with a request limit and window size."""
        super().__init__(app)
        self._limit = limit
        self._window = window_seconds
        self._hits: dict[str, tuple[int, float]] = {}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Reject the request with 429 when the client exceeds its window limit."""
        client = request.client.host if request.client else "unknown"
        now = monotonic()
        count, window_start = self._hits.get(client, (0, now))
        if now - window_start >= self._window:
            count, window_start = 0, now
        count += 1
        self._hits[client] = (count, window_start)
        if count > self._limit:
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited", "message": "Too many requests"},
            )
        return await call_next(request)
