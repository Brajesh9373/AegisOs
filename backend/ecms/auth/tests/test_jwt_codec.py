"""Tests for the JWT token codec."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from ecms.auth import JwtTokenCodec, TokenClaims, TokenType
from ecms.shared.exceptions import AuthenticationError
from ecms.shared.ids import new_uuid

_SECRET_A = "unit-test-signing-secret-alpha-0123456789"
_SECRET_B = "unit-test-signing-secret-bravo-0123456789"


def _claims(expires_in: int = 900) -> TokenClaims:
    now = datetime.now(UTC)
    return TokenClaims(
        subject="u1",
        token_type=TokenType.ACCESS,
        issued_at=now,
        expires_at=now + timedelta(seconds=expires_in),
        jti=new_uuid(),
    )


def test_round_trip() -> None:
    codec = JwtTokenCodec(secret=_SECRET_A)
    decoded = codec.decode(codec.encode(_claims()))
    assert decoded.subject == "u1"
    assert decoded.token_type is TokenType.ACCESS


def test_expired_token_raises() -> None:
    codec = JwtTokenCodec(secret=_SECRET_A)
    token = codec.encode(_claims(expires_in=-10))
    with pytest.raises(AuthenticationError):
        codec.decode(token)


def test_unknown_key_raises() -> None:
    token = JwtTokenCodec(secret=_SECRET_A).encode(_claims())
    with pytest.raises(AuthenticationError):
        JwtTokenCodec(secret=_SECRET_B).decode(token)


def test_tampered_token_raises() -> None:
    codec = JwtTokenCodec(secret=_SECRET_A)
    token = codec.encode(_claims())
    with pytest.raises(AuthenticationError):
        codec.decode(token + "x")


def test_rotate_keeps_old_key_valid() -> None:
    codec = JwtTokenCodec(secret=_SECRET_A)
    old_token = codec.encode(_claims())
    codec.rotate()
    assert codec.decode(old_token).subject == "u1"
    assert codec.decode(codec.encode(_claims())).subject == "u1"
