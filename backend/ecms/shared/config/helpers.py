"""Configuration helper primitives (SECTION 78/96).

Small helpers for parsing environment values. The full configuration framework is built
on top of these in the configuration stage.
"""

from __future__ import annotations

import os

from ecms.shared.exceptions import ConfigurationError

__all__ = ["get_env", "parse_bool"]

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


def parse_bool(value: str) -> bool:
    """Parse a boolean from a string.

    Args:
        value: The string to parse (case-insensitive).

    Returns:
        The parsed boolean.

    Raises:
        ConfigurationError: If the value is not a recognized boolean.
    """
    lowered = value.strip().lower()
    if lowered in _TRUE_VALUES:
        return True
    if lowered in _FALSE_VALUES:
        return False
    raise ConfigurationError(f"cannot parse boolean from {value!r}")


def get_env(name: str, default: str | None = None) -> str | None:
    """Return the value of an environment variable, or ``default`` when unset."""
    return os.environ.get(name, default)
