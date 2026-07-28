"""Configuration source and service ports (SECTION 66/97)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol, runtime_checkable

from ecms.configuration.domain.version import ConfigVersion

__all__ = ["ConfigurationService", "ConfigurationSource"]


@runtime_checkable
class ConfigurationSource(Protocol):
    """A source of configuration values.

    Operations:
        load: Return configuration values contributed by this source.
    """

    def load(self) -> Mapping[str, Any]: ...


class ConfigurationService(Protocol):
    """Runtime configuration service (SECTION 66).

    Operations:
        load: Resolve and return the active configuration.
        save: Validate and persist a new configuration version.
        validate: Validate a configuration mapping, raising on error.
        reload: Re-resolve configuration from its sources (hot reload).
        watch: Register a callback invoked whenever configuration changes.
        history: Return the ordered version history.
        rollback: Restore a previous version and return it.
    """

    def load(self) -> Mapping[str, Any]: ...
    def save(self, values: Mapping[str, Any]) -> ConfigVersion: ...
    def validate(self, values: Mapping[str, Any]) -> None: ...
    def reload(self) -> Mapping[str, Any]: ...
    def watch(self, callback: Callable[[Mapping[str, Any]], None]) -> None: ...
    def history(self) -> list[ConfigVersion]: ...
    def rollback(self, version: int) -> ConfigVersion: ...
