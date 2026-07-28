from datetime import UTC, datetime

from ecms.core.episode import uko_to_episode
from ecms.core.uko import UKOMetadata, UKORelationship, UKOType, UniversalKnowledgeObject


def test_uko_to_episode_preserves_source_context() -> None:
    modified_at = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
    uko = UniversalKnowledgeObject(
        type=UKOType.TICKET,
        name="Implement JWT Authentication",
        content="Add stateless authentication with JWT tokens.",
        metadata=UKOMetadata(
            source="jira",
            source_id="ABC-123",
            created_at=datetime(2026, 7, 1, tzinfo=UTC),
            modified_at=modified_at,
            tenant_id="tenant-a",
        ),
        relationships=[
            UKORelationship(
                target_id="src/auth/service.py",
                relationship="references",
                target_type=UKOType.FUNCTION,
            )
        ],
    )

    episode = uko_to_episode(uko)

    assert episode.name == "jira:ticket:Implement JWT Authentication"
    assert episode.reference_time == modified_at
    assert episode.group_id == "tenant-a"
    assert "Source ID: ABC-123" in episode.episode_body
    assert "references -> function:src/auth/service.py" in episode.episode_body
