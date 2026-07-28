"""Configuration sources and layered resolution (SECTION 78/97).

Configuration is resolved from files (YAML or JSON) and environment variables with a
defined precedence, then ``${VAR}`` placeholders are replaced with secret values.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from ecms.shared.exceptions import ConfigurationError
from ecms.shared.utils import deep_merge

__all__ = ["EnvSource", "FileSource", "inject_secrets", "resolve_config"]

_SECRET_PATTERN = re.compile(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\}")


class FileSource:
    """Loads configuration from a YAML or JSON file."""

    def __init__(self, path: Path) -> None:
        """Initialize the source for the given YAML or JSON file path."""
        self._path = path

    def load(self) -> Mapping[str, Any]:
        """Return the parsed file contents, or an empty mapping when absent.

        Raises:
            ConfigurationError: If the file is malformed or not a mapping.
        """
        if not self._path.exists():
            return {}
        text = self._path.read_text(encoding="utf-8")
        try:
            if self._path.suffix in {".yaml", ".yml"}:
                data = yaml.safe_load(text) or {}
            elif self._path.suffix == ".json":
                data = json.loads(text)
            else:
                message = f"unsupported configuration file type: {self._path}"
                raise ConfigurationError(message)
        except (yaml.YAMLError, json.JSONDecodeError) as exc:
            raise ConfigurationError(f"invalid configuration file {self._path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigurationError(f"configuration file {self._path} must contain a mapping")
        return data


class EnvSource:
    """Loads configuration from prefixed environment variables."""

    def __init__(
        self,
        prefix: str = "ECMS_",
        environ: Mapping[str, str] | None = None,
    ) -> None:
        """Initialize the source with a variable prefix and environment mapping."""
        self._prefix = prefix
        self._environ = environ if environ is not None else os.environ

    def load(self) -> Mapping[str, Any]:
        """Return variables with the prefix stripped and keys lower-cased."""
        result: dict[str, Any] = {}
        for key, value in self._environ.items():
            if key.startswith(self._prefix):
                result[key[len(self._prefix) :].lower()] = value
        return result


def inject_secrets(
    values: Mapping[str, Any],
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Replace ``${VAR}`` placeholders in string values with environment values.

    Raises:
        ConfigurationError: If a referenced environment variable is not set.
    """
    env = environ if environ is not None else os.environ

    def _replace(match: re.Match[str]) -> str:
        name = match.group("name")
        if name not in env:
            raise ConfigurationError(f"missing secret for placeholder ${{{name}}}")
        return env[name]

    def _resolve(value: Any) -> Any:
        if isinstance(value, str):
            return _SECRET_PATTERN.sub(_replace, value)
        if isinstance(value, Mapping):
            return {key: _resolve(item) for key, item in value.items()}
        if isinstance(value, list):
            return [_resolve(item) for item in value]
        return value

    return {key: _resolve(value) for key, value in values.items()}


def resolve_config(
    config_dir: Path,
    profile: str,
    *,
    prefix: str = "ECMS_",
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Resolve configuration by merging base and profile files then environment.

    Precedence, from lowest to highest: ``base`` file, ``{profile}`` file, environment
    variables. ``${VAR}`` placeholders are then replaced with secret values.

    Args:
        config_dir: Directory containing ``base.yaml`` and ``{profile}.yaml``.
        profile: The active deployment profile.
        prefix: Environment-variable prefix.
        environ: Environment mapping (defaults to ``os.environ``).

    Returns:
        The resolved configuration mapping.
    """
    base = FileSource(config_dir / "base.yaml").load()
    profile_values = FileSource(config_dir / f"{profile}.yaml").load()
    env_values = EnvSource(prefix, environ).load()
    merged = deep_merge(deep_merge(dict(base), dict(profile_values)), dict(env_values))
    return inject_secrets(merged, environ)
