"""Layered configuration service with versioning and hot reload (SECTION 66/97)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from ecms.configuration.domain.version import ConfigVersion
from ecms.configuration.infrastructure.sources import resolve_config
from ecms.shared.exceptions import ConfigurationError, ValidationError

__all__ = ["LayeredConfigurationService"]

Validator = Callable[[Mapping[str, Any]], None]
Listener = Callable[[Mapping[str, Any]], None]


class LayeredConfigurationService:
    """Resolves layered configuration and maintains a versioned history (SECTION 66/97).

    The service resolves configuration from files and environment variables, records each
    change as an immutable version, notifies registered watchers, and supports rollback.
    """

    def __init__(
        self,
        config_dir: Path,
        profile: str,
        *,
        validator: Validator | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        """Initialize the service for a configuration directory and profile."""
        self._config_dir = config_dir
        self._profile = profile
        self._validator = validator
        self._environ = environ
        self._history: list[ConfigVersion] = []
        self._listeners: list[Listener] = []
        self._current: dict[str, Any] = {}

    def load(self) -> Mapping[str, Any]:
        """Return the active configuration, resolving it on first access."""
        if not self._history:
            self.reload()
        return self._current

    def reload(self) -> Mapping[str, Any]:
        """Re-resolve configuration from its sources and record a new version."""
        values = resolve_config(self._config_dir, self._profile, environ=self._environ)
        self._commit(values)
        return self._current

    def save(self, values: Mapping[str, Any]) -> ConfigVersion:
        """Validate and persist a new configuration version."""
        self.validate(values)
        return self._commit(dict(values))

    def validate(self, values: Mapping[str, Any]) -> None:
        """Validate a configuration mapping using the registered validator.

        Raises:
            ConfigurationError: If validation fails.
        """
        if self._validator is None:
            return
        try:
            self._validator(values)
        except (ValidationError, ValueError) as exc:
            raise ConfigurationError(f"configuration validation failed: {exc}") from exc

    def watch(self, callback: Listener) -> None:
        """Register a callback invoked whenever configuration changes."""
        self._listeners.append(callback)

    def history(self) -> list[ConfigVersion]:
        """Return the ordered configuration version history."""
        return list(self._history)

    def rollback(self, version: int) -> ConfigVersion:
        """Restore a previous configuration version.

        Raises:
            ConfigurationError: If the requested version does not exist.
        """
        for record in self._history:
            if record.version == version:
                return self._commit(dict(record.values))
        raise ConfigurationError(f"unknown configuration version: {version}")

    def _commit(self, values: dict[str, Any]) -> ConfigVersion:
        record = ConfigVersion(version=len(self._history) + 1, values=values)
        self._history.append(record)
        self._current = values
        for listener in self._listeners:
            listener(values)
        return record
