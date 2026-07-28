"""Tests for ``ecms.configuration`` sources."""

from __future__ import annotations

from pathlib import Path

import pytest

from ecms.configuration.infrastructure.sources import (
    EnvSource,
    FileSource,
    inject_secrets,
    resolve_config,
)
from ecms.shared.exceptions import ConfigurationError


def test_file_source_yaml(tmp_path: Path) -> None:
    path = tmp_path / "base.yaml"
    path.write_text("a: 1\nnested:\n  x: 2\n", encoding="utf-8")
    assert FileSource(path).load() == {"a": 1, "nested": {"x": 2}}


def test_file_source_missing_returns_empty(tmp_path: Path) -> None:
    assert FileSource(tmp_path / "nope.yaml").load() == {}


def test_env_source_strips_prefix() -> None:
    source = EnvSource("ECMS_", {"ECMS_DEBUG": "true", "OTHER": "x"})
    assert source.load() == {"debug": "true"}


def test_inject_secrets_replaces_placeholder() -> None:
    assert inject_secrets({"db": "${DB_PASS}"}, {"DB_PASS": "secret"}) == {"db": "secret"}


def test_inject_secrets_missing_raises() -> None:
    with pytest.raises(ConfigurationError):
        inject_secrets({"db": "${MISSING}"}, {})


def test_resolve_config_precedence(tmp_path: Path) -> None:
    (tmp_path / "base.yaml").write_text("a: 1\nb: 1\n", encoding="utf-8")
    (tmp_path / "production.yaml").write_text("b: 2\n", encoding="utf-8")
    result = resolve_config(tmp_path, "production", environ={"ECMS_C": "3"})
    assert result == {"a": 1, "b": 2, "c": "3"}


def test_file_source_json(tmp_path: Path) -> None:
    path = tmp_path / "base.json"
    path.write_text('{"a": 1}', encoding="utf-8")
    assert FileSource(path).load() == {"a": 1}


def test_file_source_unsupported_suffix(tmp_path: Path) -> None:
    path = tmp_path / "base.txt"
    path.write_text("a", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        FileSource(path).load()


def test_file_source_invalid_yaml(tmp_path: Path) -> None:
    path = tmp_path / "base.yaml"
    path.write_text("a: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        FileSource(path).load()


def test_file_source_non_mapping(tmp_path: Path) -> None:
    path = tmp_path / "base.yaml"
    path.write_text("- 1\n- 2\n", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        FileSource(path).load()


def test_inject_secrets_recurses_lists_and_preserves_non_strings() -> None:
    result = inject_secrets({"items": ["${A}", 5], "n": 10}, {"A": "x"})
    assert result == {"items": ["x", 5], "n": 10}
