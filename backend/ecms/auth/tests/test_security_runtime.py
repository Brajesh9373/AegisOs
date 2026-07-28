"""Tests for the security runtime extensions (SECTION 218/220/222/223)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from cryptography.exceptions import InvalidTag

from ecms.auth import ComplianceEngine, EncryptionService, SecurityAnalytics
from ecms.auth.events.security_events import authentication_failed, secret_rotated
from ecms.shared.enums import EventCategory
from ecms.shared.time import utcnow


def test_encryption_round_trip_and_nonce_uniqueness() -> None:
    service = EncryptionService()
    token = service.encrypt("super secret")
    assert service.decrypt(token) == "super secret"
    assert service.encrypt("super secret") != token


def test_encryption_rotation_invalidates_old_tokens() -> None:
    service = EncryptionService()
    token = service.encrypt("data")
    service.rotate_key()
    with pytest.raises(InvalidTag):
        service.decrypt(token)


def test_compliance_legal_hold_blocks_forget() -> None:
    engine = ComplianceEngine()
    engine.place_legal_hold("user-1")
    assert engine.forget("user-1") is False
    engine.release_legal_hold("user-1")
    assert engine.forget("user-1") is True
    assert engine.is_forgotten("user-1")


def test_compliance_retention_expiry() -> None:
    engine = ComplianceEngine()
    old = utcnow() - timedelta(days=40)
    assert engine.retention_expired(old, retention_days=30) is True
    assert engine.retention_expired(utcnow(), retention_days=30) is False


def test_security_analytics_counters() -> None:
    analytics = SecurityAnalytics()
    analytics.record("auth_failed")
    analytics.record("auth_failed")
    analytics.record("authz_denied")
    assert analytics.snapshot()["auth_failed"] == 2
    assert analytics.total == 3


def test_security_events_use_security_category() -> None:
    assert authentication_failed("alice").event_category is EventCategory.SECURITY
    assert secret_rotated("api_key").event_type == "SecretRotated"
