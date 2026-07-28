"""Security analytics (SECTION 223).

Collects counters for security-relevant signals - authentication attempts,
authorization failures, permission violations and suspicious activity.
"""

from __future__ import annotations

from collections import Counter

__all__ = ["SecurityAnalytics"]


class SecurityAnalytics:
    """Aggregates security signal counters (SECTION 223)."""

    def __init__(self) -> None:
        """Initialize with empty counters."""
        self._counters: Counter[str] = Counter()

    def record(self, signal: str) -> None:
        """Record one occurrence of a security signal."""
        self._counters[signal] += 1

    def snapshot(self) -> dict[str, int]:
        """Return a copy of the current counters."""
        return dict(self._counters)

    @property
    def total(self) -> int:
        """Return the total number of recorded signals."""
        return sum(self._counters.values())
