"""Identifier and correlation-id generators (SECTION 96)."""

from __future__ import annotations

from uuid import uuid4

from ecms.shared.exceptions import ValidationError

__all__ = ["new_correlation_id", "new_id", "new_uuid"]


def new_uuid() -> str:
    """Return a new random UUID4 as a string."""
    return str(uuid4())


def new_id(prefix: str) -> str:
    """Return a new prefixed identifier such as ``task-<uuid4>``.

    Args:
        prefix: A short, non-empty token identifying the object kind. Must not
            contain whitespace.

    Returns:
        A globally-unique identifier of the form ``{prefix}-{uuid4}``.

    Raises:
        ValidationError: If ``prefix`` is empty or contains whitespace.
    """
    if not prefix or any(char.isspace() for char in prefix):
        raise ValidationError(f"invalid id prefix: {prefix!r}")
    return f"{prefix}-{uuid4()}"


def new_correlation_id() -> str:
    """Return a new correlation identifier used to trace an entire workflow."""
    return f"corr-{uuid4()}"
