"""Security control tests (SECTION 79/84)."""

from __future__ import annotations

from ecms.auth import (
    Identity,
    JwtAuthenticationService,
    JwtTokenCodec,
    PolicyAuthorizationService,
)
from ecms.shared.security import REDACTED, redact_mapping

_TEST_SECRET = "security-test-signing-secret-0123456789"


def _auth() -> JwtAuthenticationService:
    return JwtAuthenticationService(JwtTokenCodec(secret=_TEST_SECRET))


def test_tampered_token_rejected() -> None:
    service = _auth()
    pair = service.login(Identity(subject="u"))
    assert not service.validate(pair.access_token + "tampered")


def test_revoked_token_rejected() -> None:
    service = _auth()
    pair = service.login(Identity(subject="u"))
    service.revoke(pair.access_token)
    assert not service.validate(pair.access_token)


def test_authorization_is_default_deny() -> None:
    authz = PolicyAuthorizationService()
    assert not authz.check(subject="u", roles=[], resource="secret", action="read")


def test_sensitive_values_are_redacted() -> None:
    scrubbed = redact_mapping({"password": "p", "access_token": "t", "name": "ok"})
    assert scrubbed["password"] == REDACTED
    assert scrubbed["access_token"] == REDACTED
    assert scrubbed["name"] == "ok"
