"""Security utilities: secret redaction and constant-time comparison (SECTION 76/79).

These helpers keep secrets and sensitive personal information out of logs and provide a
timing-attack-resistant string comparison for tokens and signatures.
"""

from __future__ import annotations

import hmac
from collections.abc import Mapping
from typing import Any

__all__ = [
    "REDACTED",
    "SENSITIVE_KEYS",
    "constant_time_compare",
    "redact",
    "redact_mapping",
]

REDACTED = "***REDACTED***"
"""Marker substituted in place of a redacted sensitive value."""

SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "client_secret",
        "token",
        "access_token",
        "refresh_token",
        "session_token",
        "api_key",
        "apikey",
        "authorization",
        "private_key",
        "credential",
        "credentials",
    }
)
"""Substrings that mark a mapping key as carrying sensitive data."""


def redact(value: object) -> str:
    """Return the redaction marker, discarding the sensitive ``value``.

    Args:
        value: The sensitive value to discard. It is never inspected or logged.

    Returns:
        The constant :data:`REDACTED` marker.
    """
    del value
    return REDACTED


def _is_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in SENSITIVE_KEYS)


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deep copy of ``data`` with sensitive values redacted.

    Keys whose name matches a known sensitive marker have their values replaced with
    :data:`REDACTED`. Nested mappings are redacted recursively.

    Args:
        data: The mapping to redact.

    Returns:
        A new dictionary safe for structured logging.
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        if _is_sensitive(key):
            result[key] = REDACTED
        elif isinstance(value, Mapping):
            result[key] = redact_mapping(value)
        else:
            result[key] = value
    return result


def constant_time_compare(left: str, right: str) -> bool:
    """Compare two strings in constant time to mitigate timing attacks.

    Args:
        left: First string.
        right: Second string.

    Returns:
        ``True`` if the strings are equal, ``False`` otherwise.
    """
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))
