"""Strict fan-in invariants for atomic connector graph publication."""

from __future__ import annotations

from dataclasses import dataclass

_FAILED = frozenset({"failed", "cancelled"})
_PARTITION_TERMINAL = frozenset({"committed", "failed", "cancelled", "superseded"})
_BATCH_TERMINAL = frozenset({"committed", "failed", "cancelled"})


@dataclass(frozen=True, slots=True)
class FanInDecision:
    """Derived parent action from durable child state."""

    ready_to_publish: bool
    terminal_failure: bool
    reason: str


def reconcile_fan_in(
    *,
    partition_states: dict[str, int],
    batch_states: dict[str, int],
    expected_partitions: int,
) -> FanInDecision:
    """Permit publication only after exact, successful child reconciliation."""
    if expected_partitions < 1:
        return FanInDecision(False, True, "manifest has no partitions")
    partition_total = sum(partition_states.values())
    if partition_total != expected_partitions:
        return FanInDecision(False, True, "partition count does not match manifest")
    if any(partition_states.get(state, 0) for state in _FAILED):
        return FanInDecision(False, True, "partition failed or was cancelled")
    unknown_partitions = set(partition_states) - (
        _PARTITION_TERMINAL | frozenset({"pending", "claimed", "extracting", "staged", "retry"})
    )
    if unknown_partitions:
        return FanInDecision(False, True, "unknown partition state")
    if partition_states.get("superseded", 0):
        return FanInDecision(False, True, "partition was superseded")
    if partition_states.get("committed", 0) != expected_partitions:
        return FanInDecision(False, False, "partitions are still active")

    if any(batch_states.get(state, 0) for state in _FAILED):
        return FanInDecision(False, True, "staged batch failed or was cancelled")
    unknown_batches = set(batch_states) - (_BATCH_TERMINAL | frozenset({"staged", "writing"}))
    if unknown_batches:
        return FanInDecision(False, True, "unknown staged-batch state")
    if batch_states.get("staged", 0) or batch_states.get("writing", 0):
        return FanInDecision(False, False, "graph batches are still active")
    return FanInDecision(True, False, "all partitions and batches committed")
