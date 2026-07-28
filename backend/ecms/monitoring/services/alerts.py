"""Alert engine (SECTION 233).

Evaluates configurable rules against a metrics snapshot and returns the alerts
that fired. Rules are pure predicates over the metrics, keeping alerting
deterministic and testable.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

__all__ = ["Alert", "AlertEngine", "AlertRule"]

AlertPredicate = Callable[[Mapping[str, float]], bool]


@dataclass(frozen=True, slots=True)
class AlertRule:
    """A named alert rule: a severity and a predicate over metrics (SECTION 233)."""

    name: str
    severity: str
    predicate: AlertPredicate


@dataclass(frozen=True, slots=True)
class Alert:
    """A fired alert."""

    name: str
    severity: str
    message: str


class AlertEngine:
    """Evaluates alert rules against a metrics snapshot (SECTION 233)."""

    def __init__(self) -> None:
        """Initialize with no rules."""
        self._rules: list[AlertRule] = []

    def add_rule(self, name: str, severity: str, predicate: AlertPredicate) -> None:
        """Register an alert rule."""
        self._rules.append(AlertRule(name=name, severity=severity, predicate=predicate))

    def evaluate(self, metrics: Mapping[str, float]) -> list[Alert]:
        """Return the alerts whose predicate matches the metrics snapshot."""
        return [
            Alert(
                name=rule.name,
                severity=rule.severity,
                message=f"alert '{rule.name}' triggered",
            )
            for rule in self._rules
            if rule.predicate(metrics)
        ]
