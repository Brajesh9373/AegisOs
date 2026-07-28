"""Tests for ``ecms.shared.exceptions``."""

from __future__ import annotations

from ecms.shared.exceptions import EcmsError, NotFoundError, ValidationError


def test_base_error_defaults() -> None:
    err = EcmsError()
    assert err.code == "ecms_error"
    assert err.message
    assert err.details == {}


def test_custom_message_code_and_details() -> None:
    err = ValidationError("bad", details={"field": "name"})
    assert err.message == "bad"
    assert err.code == "validation_error"
    assert err.to_dict() == {
        "error": "validation_error",
        "message": "bad",
        "details": {"field": "name"},
    }


def test_subclasses_derive_from_base() -> None:
    assert isinstance(NotFoundError(), EcmsError)
    assert NotFoundError().code == "not_found"
