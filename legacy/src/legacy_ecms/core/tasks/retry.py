import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 3
    base_delay_seconds: float = 0.1
    backoff_factor: float = 2.0


async def retry_async(operation: Callable[[], Awaitable[T]], policy: RetryPolicy | None = None) -> T:
    active_policy = policy or RetryPolicy()
    last_error: Exception | None = None
    for attempt in range(active_policy.attempts):
        try:
            return await operation()
        except Exception as exc:
            last_error = exc
            if attempt == active_policy.attempts - 1:
                break
            delay = active_policy.base_delay_seconds * (active_policy.backoff_factor**attempt)
            await asyncio.sleep(delay)
    assert last_error is not None
    raise last_error
