"""Diagnostics engine (SECTION 232).

Runs registered dependency probes (database, cache, broker, graph, connectors)
and reports an aggregate readiness result. A failing probe is reported, never
raised, so diagnostics never take the process down.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

__all__ = ["DiagnosticsEngine"]

Probe = Callable[[], Awaitable[bool]]


class DiagnosticsEngine:
    """Runs dependency probes and aggregates readiness (SECTION 232)."""

    def __init__(self) -> None:
        """Initialize with no registered probes."""
        self._probes: dict[str, Probe] = {}

    def register(self, name: str, probe: Probe) -> None:
        """Register a named readiness probe."""
        self._probes[name] = probe

    async def run(self) -> dict[str, Any]:
        """Run every probe and return per-check results and an overall verdict."""
        checks: dict[str, bool] = {}
        for name, probe in self._probes.items():
            try:
                checks[name] = await probe()
            except Exception:  # a failing probe is reported, never raised
                checks[name] = False
        return {"healthy": all(checks.values()) if checks else True, "checks": checks}
