"""Secrets provider (SECTION 78/79/106)."""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

from ecms.shared.exceptions import ConfigurationError

__all__ = ["EnvSecretsProvider", "SecretsProvider"]


@runtime_checkable
class SecretsProvider(Protocol):
    """Provides secret values by name.

    Operations:
        get_secret: Return a secret by name, raising when absent.
        try_get_secret: Return a secret by name, or a default when absent.
    """

    def get_secret(self, name: str) -> str: ...
    def try_get_secret(self, name: str, default: str | None = None) -> str | None: ...


class EnvSecretsProvider:
    """Reads secrets from environment variables (optionally prefixed)."""

    def __init__(self, prefix: str = "") -> None:
        """Initialize with an optional environment-variable prefix."""
        self._prefix = prefix

    def get_secret(self, name: str) -> str:
        """Return a secret, raising ``ConfigurationError`` when it is not set."""
        value = os.environ.get(f"{self._prefix}{name}")
        if value is None:
            raise ConfigurationError(f"missing secret: {name}")
        return value

    def try_get_secret(self, name: str, default: str | None = None) -> str | None:
        """Return a secret, or ``default`` when it is not set."""
        return os.environ.get(f"{self._prefix}{name}", default)
