from collections import deque
from datetime import UTC, datetime, timedelta


class RateLimiter:
    """In-memory sliding-window rate limiter."""

    def __init__(self, max_events: int, window_seconds: int = 60) -> None:
        self.max_events = max_events
        self.window = timedelta(seconds=window_seconds)
        self._events: deque[datetime] = deque()

    def allow(self) -> bool:
        now = datetime.now(UTC)
        cutoff = now - self.window
        while self._events and self._events[0] <= cutoff:
            self._events.popleft()
        if len(self._events) >= self.max_events:
            return False
        self._events.append(now)
        return True
