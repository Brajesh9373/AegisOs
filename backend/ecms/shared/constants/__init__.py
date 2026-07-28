"""Shared constants for the ECMS platform."""

from __future__ import annotations

from typing import Final

__all__ = [
    "DEFAULT_ENCODING",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "PLATFORM_NAME",
]

PLATFORM_NAME: Final = "ecms"
"""Canonical platform name used in logs, metrics and service identifiers."""

DEFAULT_PAGE_SIZE: Final = 50
"""Default number of items returned by paginated APIs."""

MAX_PAGE_SIZE: Final = 500
"""Maximum number of items a single paginated response may return."""

DEFAULT_ENCODING: Final = "utf-8"
"""Default text encoding used throughout the platform."""
