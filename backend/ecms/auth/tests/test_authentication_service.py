"""Tests for the JWT authentication service."""

from __future__ import annotations

import pytest

from ecms.auth import (
    Identity,
    JwtAuthenticationService,
    JwtTokenCodec,
    PrincipalType,
    TokenType,
)
from ecms.shared.exceptions import AuthenticationError


def _service() -> JwtAuthenticationService:
    return JwtAuthenticationService(JwtTokenCodec(secret="unit-test-signing-secret-0123456789abcd"))


def _identity() -> Identity:
    return Identity(subject="u1", roles=["admin"], scopes=["read"])


def test_login_and_verify() -> None:
    service = _service()
    pair = service.login(_identity())
    identity = service.verify(pair.access_token)
    assert identity.subject == "u1"
    assert identity.roles == ["admin"]


def test_validate() -> None:
    service = _service()
    pair = service.login(_identity())
    assert service.validate(pair.access_token)
    assert not service.validate("garbage")


def test_refresh_rotates_and_revokes_old() -> None:
    service = _service()
    pair = service.login(_identity())
    new_pair = service.refresh(pair.refresh_token)
    assert new_pair.access_token
    with pytest.raises(AuthenticationError):
        service.refresh(pair.refresh_token)


def test_refresh_rejects_access_token() -> None:
    service = _service()
    pair = service.login(_identity())
    with pytest.raises(AuthenticationError):
        service.refresh(pair.access_token)


def test_logout_revokes_token() -> None:
    service = _service()
    pair = service.login(_identity())
    service.logout(pair.access_token)
    assert not service.validate(pair.access_token)


def test_issue_service_token() -> None:
    service = _service()
    identity = Identity(subject="svc-1", principal_type=PrincipalType.SERVICE)
    token = service.issue_token(identity, TokenType.SERVICE, ttl=60)
    assert service.verify(token).principal_type is PrincipalType.SERVICE


def test_rotate_keys_then_verify_new_tokens() -> None:
    service = _service()
    service.rotate_keys()
    pair = service.login(_identity())
    assert service.verify(pair.access_token).subject == "u1"
