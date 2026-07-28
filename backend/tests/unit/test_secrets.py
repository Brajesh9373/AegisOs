"""Tests for the secrets provider."""

from __future__ import annotations

import pytest

from ecms.infrastructure.secrets import EnvSecretsProvider
from ecms.shared.exceptions import ConfigurationError


def test_get_secret_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ECMS_TEST_SECRET", "value")
    provider = EnvSecretsProvider(prefix="ECMS_")
    assert provider.get_secret("TEST_SECRET") == "value"


def test_get_secret_missing_raises() -> None:
    with pytest.raises(ConfigurationError):
        EnvSecretsProvider().get_secret("DEFINITELY_MISSING_XYZ")


def test_try_get_secret_default() -> None:
    assert EnvSecretsProvider().try_get_secret("MISSING_XYZ", "fallback") == "fallback"
