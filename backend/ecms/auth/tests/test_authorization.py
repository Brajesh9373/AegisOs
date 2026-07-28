"""Tests for the policy authorization service."""

from __future__ import annotations

from ecms.auth import AccessRequest, Identity, PolicyAuthorizationService, Role
from ecms.shared.enums import SecurityClassification
from ecms.shared.models import SecurityPolicy


def test_default_deny() -> None:
    authz = PolicyAuthorizationService()
    assert not authz.check(subject="u1", roles=[], resource="knowledge", action="read")


def test_rbac_grant() -> None:
    authz = PolicyAuthorizationService()
    authz.grant("reader", "knowledge:read")
    assert authz.check(subject="u1", roles=["reader"], resource="knowledge", action="read")
    assert not authz.check(subject="u1", roles=["reader"], resource="knowledge", action="write")


def test_wildcard_permission() -> None:
    authz = PolicyAuthorizationService()
    authz.grant("admin", "*:*")
    assert authz.check(subject="a", roles=["admin"], resource="anything", action="delete")


def test_explicit_deny_wins() -> None:
    authz = PolicyAuthorizationService()
    authz.grant("reader", "knowledge:read")
    authz.deny("knowledge", "read", roles=["reader"])
    assert not authz.check(subject="u1", roles=["reader"], resource="knowledge", action="read")


def test_permissions_and_roles() -> None:
    authz = PolicyAuthorizationService()
    authz.grant("reader", "knowledge:read")
    assert "knowledge:read" in authz.permissions("reader")
    assert any(role.name == "reader" for role in authz.roles())
    assert authz.permissions("missing") == []


def test_policies_listing() -> None:
    authz = PolicyAuthorizationService()
    authz.deny("x", "y")
    assert len(authz.policies()) == 1


def test_abac_allow_condition() -> None:
    authz = PolicyAuthorizationService()
    authz.allow("doc", "read", conditions={"tenant": "acme"})
    allowed = authz.authorize(
        AccessRequest(subject="u", resource="doc", action="read", attributes={"tenant": "acme"}),
    )
    denied = authz.authorize(
        AccessRequest(subject="u", resource="doc", action="read", attributes={"tenant": "other"}),
    )
    assert allowed.allowed
    assert not denied.allowed


def test_audit_hook_called() -> None:
    seen: list[bool] = []
    authz = PolicyAuthorizationService(
        audit_hook=lambda _req, decision: seen.append(decision.allowed)
    )
    authz.check(subject="u", roles=[], resource="r", action="a")
    assert seen == [False]


def test_knowledge_access_public() -> None:
    authz = PolicyAuthorizationService()
    policy = SecurityPolicy(classification=SecurityClassification.PUBLIC)
    assert authz.knowledge_access(Identity(subject="u"), policy)


def test_knowledge_access_by_role() -> None:
    authz = PolicyAuthorizationService()
    identity = Identity(subject="u", roles=["analyst"])
    policy = SecurityPolicy(
        classification=SecurityClassification.CONFIDENTIAL,
        allowed_roles=["analyst"],
    )
    assert authz.knowledge_access(identity, policy)


def test_knowledge_access_denied() -> None:
    authz = PolicyAuthorizationService()
    identity = Identity(subject="u", roles=["intern"])
    policy = SecurityPolicy(
        classification=SecurityClassification.CONFIDENTIAL,
        allowed_roles=["analyst"],
    )
    assert not authz.knowledge_access(identity, policy)


def test_register_role_and_grant_appends() -> None:
    authz = PolicyAuthorizationService()
    authz.register_role(Role(name="editor", permissions=["doc:write"]))
    assert authz.check(subject="u", roles=["editor"], resource="doc", action="write")
    authz.grant("editor", "doc:read")
    assert authz.check(subject="u", roles=["editor"], resource="doc", action="read")


def test_knowledge_access_by_principal() -> None:
    authz = PolicyAuthorizationService()
    policy = SecurityPolicy(
        classification=SecurityClassification.CONFIDENTIAL,
        allowed_principals=["u1"],
    )
    assert authz.knowledge_access(Identity(subject="u1"), policy)


def test_deny_policy_scoped_to_roles() -> None:
    authz = PolicyAuthorizationService()
    authz.grant("reader", "res:act")
    authz.deny("res", "act", roles=["blocked"])
    assert authz.check(subject="u", roles=["reader"], resource="res", action="act")
    assert not authz.check(subject="u", roles=["blocked", "reader"], resource="res", action="act")


def test_deny_policy_scoped_to_subjects() -> None:
    authz = PolicyAuthorizationService()
    authz.grant("reader", "res:act")
    authz.deny("res", "act", subjects=["banned"])
    assert authz.check(subject="ok", roles=["reader"], resource="res", action="act")
    assert not authz.check(subject="banned", roles=["reader"], resource="res", action="act")
