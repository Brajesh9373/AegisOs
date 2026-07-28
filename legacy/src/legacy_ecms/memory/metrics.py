"""Memory layer metrics — lightweight counters for observability."""
from __future__ import annotations

import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable


class MemoryMetrics:
    """Lightweight in-process metrics for memory operations.

    For production, integrate with Prometheus/OpenTelemetry via
    the existing metrics middleware.
    """

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._timings: dict[str, list[float]] = defaultdict(list)

    def increment(self, key: str, value: int = 1) -> None:
        self._counters[key] += value

    def record_timing(self, key: str, elapsed: float) -> None:
        self._timings[key].append(elapsed)

    def snapshot(self) -> dict[str, Any]:
        """Return current metrics snapshot for /metrics endpoint."""
        result: dict[str, Any] = {"counters": dict(self._counters)}
        for k, vals in self._timings.items():
            if vals:
                result[f"{k}_avg_ms"] = round(sum(vals) / len(vals) * 1000, 2)
                result[f"{k}_p95_ms"] = round(sorted(vals)[int(len(vals) * 0.95)] * 1000, 2) if len(vals) >= 20 else None
        return result


# Global instance
metrics = MemoryMetrics()


def timed(key: str) -> Callable:
    """Decorator to record timing + counter for async methods."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                metrics.increment(f"{key}.success")
                return result
            except Exception as exc:
                metrics.increment(f"{key}.error")
                raise
            finally:
                metrics.record_timing(key, time.perf_counter() - start)
        return wrapper
    return decorator
