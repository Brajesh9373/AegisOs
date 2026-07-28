from datetime import UTC, datetime

from fastapi.testclient import TestClient

import ecms.api.graph_context as graph_context
from ecms.core.uko import UKOMetadata, UKOType, UniversalKnowledgeObject
from ecms.main import create_app
from tests.fakes import FakeGraphClient


def test_provider_catalog_lists_git_provider() -> None:
    client = TestClient(create_app())

    response = client.get("/providers")

    assert response.status_code == 200
    assert response.json()[0]["name"] == "git"


def test_console_ui_is_served() -> None:
    client = TestClient(create_app())

    response = client.get("/")
    script = client.get("/assets/app.js")

    assert response.status_code == 200
    assert "ECMS Console" in response.text
    assert script.status_code == 200
    assert "gitForm" in script.text


def test_ingest_uko_returns_structural_episode_names() -> None:
    client = TestClient(create_app())
    uko = UniversalKnowledgeObject(
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

    response = client.post("/ingest/uko", json={"uko": uko.model_dump(mode="json")})

    assert response.status_code == 200
    assert response.json()["episode_count"] == 3
    assert response.json()["persisted"] is False
    assert "git:function:authenticate_user" in response.json()["episode_names"]
    assert "semantic:concept:Authentication" in response.json()["episode_names"]


def test_ingest_uko_persists_episodes_when_requested(monkeypatch) -> None:
    FakeGraphClient.reset()
    monkeypatch.setattr(graph_context, "create_graph_client", lambda: FakeGraphClient())
    client = TestClient(create_app())
    uko = UniversalKnowledgeObject(
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

    response = client.post(
        "/ingest/uko",
        json={"uko": uko.model_dump(mode="json"), "persist": True},
    )

    assert response.status_code == 200
    assert response.json()["persisted"] is True
    assert FakeGraphClient.instances[0].initialized
    assert FakeGraphClient.instances[0].closed
    assert len(FakeGraphClient.instances[0].episodes) == response.json()["episode_count"]
