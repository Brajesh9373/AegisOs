"""Tests for ``ecms.configuration`` settings."""

from __future__ import annotations

import pytest

from ecms.configuration import AppSettings, Profile, get_settings, reload_settings


def test_default_settings() -> None:
    settings = AppSettings()
    assert settings.app_name == "ecms"
    assert settings.environment is Profile.DEVELOPMENT
    assert settings.debug is False


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ECMS_DEBUG", "true")
    monkeypatch.setenv("ECMS_ENVIRONMENT", "production")
    settings = reload_settings()
    assert settings.debug is True
    assert settings.environment is Profile.PRODUCTION
    get_settings.cache_clear()
