"""UTC-first time utilities (SECTION 96)."""

from __future__ import annotations

from datetime import UTC, datetime

from ecms.shared.exceptions import ValidationError

__all__ = ["from_iso", "to_iso", "utcnow"]


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def to_iso(moment: datetime) -> str:
    """Serialize a datetime to an ISO-8601 string in UTC.

    Args:
        moment: A datetime. Naive datetimes are assumed to already be UTC.

    Returns:
        An ISO-8601 formatted string normalized to the UTC offset.
    """
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC).isoformat()


def from_iso(value: str) -> datetime:
    """Parse an ISO-8601 string into a timezone-aware UTC datetime.

    Args:
        value: An ISO-8601 timestamp. A trailing ``Z`` designator is accepted.

    Returns:
        A timezone-aware datetime normalized to UTC.

    Raises:
        ValidationError: If ``value`` is not a valid ISO-8601 timestamp.
    """
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"invalid ISO-8601 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
