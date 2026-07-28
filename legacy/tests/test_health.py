from fastapi.testclient import TestClient

import ecms.api.routes.health as health_routes
from ecms.main import create_app
from tests.fakes import FakeGraphClient


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "ecms"


def test_graph_health_endpoint_uses_graph_client(monkeypatch) -> None:
    FakeGraphClient.reset()
    monkeypatch.setattr(health_routes, "create_graph_client", lambda: FakeGraphClient())
    client = TestClient(create_app())

    response = client.get("/health/graph")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert FakeGraphClient.instances[0].initialized
    assert FakeGraphClient.instances[0].closed
