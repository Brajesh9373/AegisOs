"""Tests for ``ecms.shared.time``."""

from __future__ import annotations

from datetime import datetime

import pytest

from ecms.shared.exceptions import ValidationError
from ecms.shared.time import from_iso, to_iso, utcnow


def test_utcnow_is_timezone_aware() -> None:
    assert utcnow().tzinfo is not None


def test_iso_round_trip_preserves_instant() -> None:
    now = utcnow()
    assert from_iso(to_iso(now)) == now


def test_from_iso_accepts_z_suffix() -> None:
    parsed = from_iso("2026-01-01T00:00:00Z")
    assert parsed.tzinfo is not None
    assert parsed.year == 2026


def test_to_iso_normalizes_naive_datetime_to_utc() -> None:
    result = to_iso(datetime(2026, 1, 1, 12, 0, 0))
    assert result.endswith("+00:00")


def test_from_iso_rejects_invalid_value() -> None:
    with pytest.raises(ValidationError):
        from_iso("not-a-timestamp")


def test_from_iso_assumes_utc_for_naive_value() -> None:
    parsed = from_iso("2026-01-01T00:00:00")
    offset = parsed.utcoffset()
    assert offset is not None
    assert offset.total_seconds() == 0
