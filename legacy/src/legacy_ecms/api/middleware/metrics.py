from collections import Counter
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestMetrics:
    def __init__(self) -> None:
        self.request_count: Counter[str] = Counter()
        self.total_latency_seconds: Counter[str] = Counter()

    def record(self, path: str, elapsed: float) -> None:
        self.request_count[path] += 1
        self.total_latency_seconds[path] += elapsed

    def snapshot(self) -> dict:
        return {
            "request_count": dict(self.request_count),
            "total_latency_seconds": dict(self.total_latency_seconds),
        }


metrics = RequestMetrics()


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = perf_counter()
        response = await call_next(request)
        metrics.record(request.url.path, perf_counter() - start)
        return response
