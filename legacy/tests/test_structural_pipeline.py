from datetime import UTC, datetime

import pytest

from ecms.core.uko import UKOMetadata, UKOType, UniversalKnowledgeObject
from ecms.pipeline.orchestrator import PipelineOrchestrator
from ecms.pipeline.structural.python_parser import PythonStructuralExtractor


PYTHON_CONTENT = '''
import jwt


class AuthService:
    """Handles authentication."""

    def authenticate_user(self, token):
        payload = jwt.decode(token, "secret", algorithms=["HS256"])
        return payload["sub"]
'''


def test_python_structural_extractor_finds_classes_functions_and_calls() -> None:
    result = PythonStructuralExtractor().extract(PYTHON_CONTENT)

    names = {artifact.name for artifact in result.artifacts}
    calls = {(relationship.source_name, relationship.target_name) for relationship in result.relationships}

    assert result.errors == []
    assert {"jwt", "AuthService", "authenticate_user"}.issubset(names)
    assert ("authenticate_user", "jwt.decode") in calls


@pytest.mark.asyncio
async def test_orchestrator_derives_structural_ukos() -> None:
    uko = UniversalKnowledgeObject(
        id="uko-git-file-auth",
        type=UKOType.FILE,
        name="src/auth.py",
        content=PYTHON_CONTENT,
        metadata=UKOMetadata(
            source="git",
            source_id="src/auth.py",
            created_at=datetime(2026, 7, 1, tzinfo=UTC),
            modified_at=datetime(2026, 7, 1, tzinfo=UTC),
        ),
    )

    episodes, _ = await PipelineOrchestrator().process_uko(uko)

    assert {episode.uko.type for episode in episodes} >= {
        UKOType.FILE,
        UKOType.CLASS,
        UKOType.FUNCTION,
        UKOType.IMPORT,
    }
    assert any(episode.uko.name == "authenticate_user" for episode in episodes)


@pytest.mark.asyncio
async def test_structural_call_relationships_are_not_business_concepts() -> None:
    uko = UniversalKnowledgeObject(
        id="uko-git-file-auth",
        type=UKOType.FILE,
        name="src/auth.py",
        content=PYTHON_CONTENT,
        metadata=UKOMetadata(
            source="git",
            source_id="src/auth.py",
            created_at=datetime(2026, 7, 1, tzinfo=UTC),
            modified_at=datetime(2026, 7, 1, tzinfo=UTC),
        ),
    )

    episodes, _ = await PipelineOrchestrator().process_uko(uko)
    function_episode = next(ep for ep in episodes if ep.uko.name == "authenticate_user")
    calls = [rel for rel in function_episode.uko.relationships if rel.relationship == "calls"]
    imports = [rel for rel in function_episode.uko.relationships if rel.relationship == "uses_import"]

    assert calls
    assert calls[0].target_type == UKOType.API
    assert imports
    assert imports[0].target_type == UKOType.IMPORT


@pytest.mark.asyncio
async def test_orchestrator_connects_class_to_method_and_method_to_class() -> None:
    uko = UniversalKnowledgeObject(
        id="uko-git-file-auth",
        type=UKOType.FILE,
        name="src/auth.py",
        content=PYTHON_CONTENT,
        metadata=UKOMetadata(
            source="git",
            source_id="src/auth.py",
            created_at=datetime(2026, 7, 1, tzinfo=UTC),
            modified_at=datetime(2026, 7, 1, tzinfo=UTC),
        ),
    )

    episodes, _ = await PipelineOrchestrator().process_uko(uko)
    class_episode = next(ep for ep in episodes if ep.uko.name == "AuthService")
    function_episode = next(ep for ep in episodes if ep.uko.name == "authenticate_user")

    assert any(
        rel.relationship == "defines_method" and rel.target_id == function_episode.uko.id
        for rel in class_episode.uko.relationships
    )
    assert any(
        rel.relationship == "defined_in" and rel.target_id == class_episode.uko.id
        for rel in function_episode.uko.relationships
    )
