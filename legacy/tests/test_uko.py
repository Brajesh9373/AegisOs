from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ecms.core.uko import UKOMetadata, UKORelationship, UKOType, UniversalKnowledgeObject


def test_universal_knowledge_object_exposes_evidence_key() -> None:
    metadata = UKOMetadata(
        source="git",
        source_id="src/auth.py:10-20",
        created_at=datetime(2026, 7, 1, tzinfo=UTC),
        modified_at=datetime(2026, 7, 2, tzinfo=UTC),
        authors=["Brajesh Patil"],
        tags=["authentication"],
    )
    uko = UniversalKnowledgeObject(
        type=UKOType.FUNCTION,
        name="authenticate_user",
        content="def authenticate_user(token): ...",
        metadata=metadata,
        relationships=[
            UKORelationship(
                target_id="person-brajesh",
                relationship="authored_by",
                target_type=UKOType.PERSON,
                confidence=0.9,
            )
        ],
    )

    assert uko.evidence_key == "git:src/auth.py:10-20"
    assert uko.id.startswith("uko-")


def test_metadata_rejects_backwards_time() -> None:
    with pytest.raises(ValidationError):
        UKOMetadata(
            source="jira",
            source_id="ABC-123",
            created_at=datetime(2026, 7, 2, tzinfo=UTC),
            modified_at=datetime(2026, 7, 1, tzinfo=UTC),
        )
