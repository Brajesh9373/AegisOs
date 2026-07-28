"""Tests for password hashing and API keys."""

from __future__ import annotations

from ecms.auth import ApiKeyManager, BcryptPasswordHasher, extract_bearer_token


def test_hash_and_verify_password() -> None:
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("s3cret")
    assert hashed != "s3cret"
    assert hasher.verify("s3cret", hashed)
    assert not hasher.verify("wrong", hashed)


def test_verify_rejects_invalid_hash() -> None:
    assert BcryptPasswordHasher().verify("x", "not-a-hash") is False


def test_api_key_generate_and_verify() -> None:
    manager = ApiKeyManager()
    key, hashed = manager.generate()
    assert key.startswith("ecms_")
    assert manager.verify(key, hashed)
    assert not manager.verify("ecms_wrong", hashed)


def test_extract_bearer_token() -> None:
    assert extract_bearer_token("Bearer abc") == "abc"
    assert extract_bearer_token("bearer abc") == "abc"
    assert extract_bearer_token("Basic abc") is None
    assert extract_bearer_token(None) is None
    assert extract_bearer_token("Bearer ") is None
