"""Tests for the ECMS CLI (SECTION 209/312)."""

from __future__ import annotations

from typer.testing import CliRunner

from ecms import __version__
from ecms.cli.app import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_roles_command_lists_worker_roles() -> None:
    result = runner.invoke(app, ["roles"])
    assert result.exit_code == 0
    assert "knowledge" in result.stdout
    assert "reflection" in result.stdout


def test_worker_check_accepts_valid_role() -> None:
    result = runner.invoke(app, ["worker", "promotion", "--check"])
    assert result.exit_code == 0
    assert "valid" in result.stdout


def test_worker_rejects_unknown_role() -> None:
    result = runner.invoke(app, ["worker", "bogus", "--check"])
    assert result.exit_code == 1
