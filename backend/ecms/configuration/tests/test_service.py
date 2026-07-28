"""Tests for the layered configuration service."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from ecms.configuration.services.configuration_service import LayeredConfigurationService
from ecms.shared.exceptions import ConfigurationError


def _service(
    tmp_path: Path,
    validator: object = None,
) -> LayeredConfigurationService:
    (tmp_path / "base.yaml").write_text("a: 1\n", encoding="utf-8")
    return LayeredConfigurationService(
        tmp_path,
        "testing",
        validator=validator,  # type: ignore[arg-type]
        environ={},
    )


def test_load_records_first_version(tmp_path: Path) -> None:
    service = _service(tmp_path)
    assert service.load()["a"] == 1
    assert len(service.history()) == 1


def test_reload_adds_version(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.load()
    service.reload()
    assert len(service.history()) == 2


def test_save_and_rollback(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.load()
    service.save({"a": 99})
    assert service.load()["a"] == 99
    restored = service.rollback(1)
    assert restored.values["a"] == 1


def test_watch_is_notified(tmp_path: Path) -> None:
    service = _service(tmp_path)
    seen: list[Mapping[str, Any]] = []
    service.watch(seen.append)
    service.load()
    assert seen and seen[0]["a"] == 1


def test_validate_failure_raises(tmp_path: Path) -> None:
    def validator(config: Mapping[str, Any]) -> None:
        if "a" not in config:
            raise ValueError("missing a")

    service = _service(tmp_path, validator=validator)
    with pytest.raises(ConfigurationError):
        service.save({"b": 1})


def test_rollback_unknown_version_raises(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.load()
    with pytest.raises(ConfigurationError):
        service.rollback(99)
