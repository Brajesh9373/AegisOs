"""Validation helpers that raise typed platform errors (SECTION 96)."""

from __future__ import annotations

from collections.abc import Collection

from ecms.shared.exceptions import ValidationError

__all__ = ["ensure_in_range", "ensure_non_empty", "ensure_one_of"]


def ensure_non_empty(value: str, *, field: str = "value") -> str:
    """Return the stripped string, raising when it is empty.

    Args:
        value: The string to validate.
        field: The field name used in the error message.

    Returns:
        The stripped, non-empty string.

    Raises:
        ValidationError: If the string is empty or whitespace-only.
    """
    stripped = value.strip()
    if not stripped:
        raise ValidationError(f"{field} must not be empty", details={"field": field})
    return stripped


def ensure_in_range(value: int, *, minimum: int, maximum: int, field: str = "value") -> int:
    """Return ``value`` when within ``[minimum, maximum]``, raising otherwise.

    Raises:
        ValidationError: If the value is out of range.
    """
    if not minimum <= value <= maximum:
        raise ValidationError(
            f"{field} must be between {minimum} and {maximum}",
            details={"field": field, "value": value},
        )
    return value


def ensure_one_of[T](value: T, options: Collection[T], *, field: str = "value") -> T:
    """Return ``value`` when it is a member of ``options``, raising otherwise.

    Raises:
        ValidationError: If the value is not one of the allowed options.
    """
    if value not in options:
        allowed = sorted(str(option) for option in options)
        raise ValidationError(
            f"{field} must be one of {allowed}",
            details={"field": field},
        )
    return value
