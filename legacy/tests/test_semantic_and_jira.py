from datetime import UTC, datetime

import pytest

from ecms.core.uko import UKOMetadata, UKOType, UniversalKnowledgeObject
from ecms.pipeline.orchestrator import PipelineOrchestrator
from ecms.pipeline.semantic.llm_extractor import KeywordSemanticExtractor
from ecms.providers.jira import JiraProvider


@pytest.mark.asyncio
async def test_keyword_semantic_extractor_finds_business_concepts() -> None:
    uko = UniversalKnowledgeObject(
        type=UKOType.TICKET,
        name="Implement JWT Authentication",
        content="Add JWT token login for customer accounts.",
        metadata=UKOMetadata(
            source="jira",
            source_id="ABC-123",
            created_at=datetime(2026, 7, 1, tzinfo=UTC),
            modified_at=datetime(2026, 7, 1, tzinfo=UTC),
        ),
    )

    result = await KeywordSemanticExtractor().extract(uko)

    assert {concept.name for concept in result.concepts} >= {"Authentication", "Customer"}


@pytest.mark.asyncio
async def test_orchestrator_filters_low_confidence_semantic_concepts() -> None:
    uko = UniversalKnowledgeObject(
        type=UKOType.FILE,
        name="profile.py",
        content="def get_user_name(user):\n    return user.name\n",
        metadata=UKOMetadata(
            source="git",
            source_id="profile.py",
            created_at=datetime(2026, 7, 1, tzinfo=UTC),
            modified_at=datetime(2026, 7, 1, tzinfo=UTC),
        ),
    )

    episodes, _ = await PipelineOrchestrator().process_uko(uko)

    assert not any(
        episode.uko.type == UKOType.CONCEPT and episode.uko.name == "Customer"
        for episode in episodes
    )


@pytest.mark.asyncio
async def test_semantic_concept_links_to_specific_supporting_artifact() -> None:
    uko = UniversalKnowledgeObject(
        id="uko-auth-file",
        type=UKOType.FILE,
        name="auth.py",
        content="def authenticate_user(token):\n    return token\n",
        metadata=UKOMetadata(
            source="git",
            source_id="auth.py",
            created_at=datetime(2026, 7, 1, tzinfo=UTC),
            modified_at=datetime(2026, 7, 1, tzinfo=UTC),
        ),
    )

    episodes, _ = await PipelineOrchestrator().process_uko(uko)
    concept = next(ep.uko for ep in episodes if ep.uko.type == UKOType.CONCEPT and ep.uko.name == "Authentication")
    function = next(ep.uko for ep in episodes if ep.uko.type == UKOType.FUNCTION)

    assert any(
        rel.relationship == "supported_by" and rel.target_id == function.id
        for rel in concept.relationships
    )


@pytest.mark.asyncio
async def test_jira_provider_syncs_tickets_and_temporal_events() -> None:
    issue = {
        "key": "ABC-123",
        "summary": "Implement JWT Authentication",
        "description": "Add stateless JWT token login.",
        "status": "In Progress",
        "labels": ["security"],
        "created": "2026-07-01T10:00:00+00:00",
        "updated": "2026-07-02T10:00:00+00:00",
        "assignee": {"displayName": "Brajesh Patil"},
        "reporter": "B. Patil",
        "changelog": [
            {
                "field": "status",
                "from": "To Do",
                "to": "In Progress",
                "created": "2026-07-02T10:00:00+00:00",
                "author": "Brajesh Patil",
            }
        ],
    }
    provider = JiraProvider([issue])

    assert await provider.validate()
    assert await provider.discover() == ["ABC"]

    ukos = [uko async for uko in provider.sync("ABC")]

    assert len(ukos) == 1
    assert ukos[0].type == UKOType.TICKET
    assert ukos[0].relationships[0].relationship == "assigned_to"

    episodes, _ = await PipelineOrchestrator().process_uko(ukos[0])
    episode_types = {episode.uko.type for episode in episodes}

    assert UKOType.CONCEPT in episode_types
    assert UKOType.EVENT in episode_types
