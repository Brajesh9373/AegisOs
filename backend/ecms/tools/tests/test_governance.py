"""Tests for the tool permission and policy engines (SECTION 175/176)."""

from __future__ import annotations

from ecms.tools import ToolPermissionEngine, ToolPolicyEngine


def test_permission_default_allow_with_deny_list() -> None:
    engine = ToolPermissionEngine(denied_tools=["terminal"])
    assert engine.check("filesystem")
    assert not engine.check("terminal")


def test_permission_default_deny_requires_grant() -> None:
    engine = ToolPermissionEngine(default_allow=False)
    assert not engine.check("filesystem")
    assert engine.check("filesystem", agent_permissions=["filesystem"])


def test_policy_allow_and_deny_commands() -> None:
    policy = ToolPolicyEngine(allowed_commands=["ls", "cat"], denied_commands=["rm"])
    assert policy.allows_command("ls")
    assert not policy.allows_command("rm")
    assert not policy.allows_command("curl")
    assert policy.timeout_seconds == 30.0


def test_policy_without_allowlist_permits_non_denied() -> None:
    policy = ToolPolicyEngine(denied_commands=["rm"])
    assert policy.allows_command("anything")
    assert not policy.allows_command("rm")
