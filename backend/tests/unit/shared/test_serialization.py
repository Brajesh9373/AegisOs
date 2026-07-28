"""Tests for ``ecms.shared.serialization``."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ecms.shared.exceptions import SerializationError
from ecms.shared.models import UniversalCognitiveObject
from ecms.shared.serialization import from_json, model_to_dict, to_json


def _uco() -> UniversalCognitiveObject:
    return UniversalCognitiveObject(
        canonical_name="A",
        display_name="A",
        ontology_type="Service",
        description="d",
    )


def test_json_round_trip() -> None:
    assert from_json(to_json({"a": 1})) == {"a": 1}


def test_to_json_serializes_model() -> None:
    parsed = from_json(to_json(_uco()))
    assert parsed["uco_id"].startswith("uco-")


def test_model_to_dict() -> None:
    assert model_to_dict(_uco())["canonical_name"] == "A"


def test_to_json_handles_datetime() -> None:
    assert "2026" in to_json({"at": datetime(2026, 1, 1, tzinfo=UTC)})


def test_from_json_invalid_raises() -> None:
    with pytest.raises(SerializationError):
        from_json("{not json}")


def test_to_json_unserializable_raises() -> None:
    with pytest.raises(SerializationError):
        to_json({1, 2, 3})
