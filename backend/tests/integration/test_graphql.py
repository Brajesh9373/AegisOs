"""Integration tests for the GraphQL gateway."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ecms.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_graphql_version(client: TestClient) -> None:
    response = client.post("/graphql", json={"query": "{ version }"})
    assert response.status_code == 200
    assert response.json()["data"]["version"]


def test_graphql_system_info(client: TestClient) -> None:
    response = client.post("/graphql", json={"query": "{ systemInfo { name version } }"})
    data = response.json()["data"]["systemInfo"]
    assert data["name"]
    assert data["version"]


def test_graphql_playground(client: TestClient) -> None:
    response = client.get("/graphql", headers={"Accept": "text/html"})
    assert response.status_code == 200
