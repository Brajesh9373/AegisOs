"""Integration tests for the REST API gateway."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ecms.api.app import create_app
from ecms.api.dependencies.providers import Pagination, get_pagination
from ecms.api.middleware.rate_limit import RateLimitMiddleware
from ecms.auth import Identity
from ecms.sdk import create_sdk


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_root_and_version(client: TestClient) -> None:
    assert "name" in client.get("/").json()
    assert client.get("/version").json()["version"]


def test_versioned_health(client: TestClient) -> None:
    assert client.get("/api/v1/health").status_code == 200


def test_metrics_endpoint(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "ecms_requests_total" in response.text


def test_correlation_header_present(client: TestClient) -> None:
    headers = {key.lower(): value for key, value in client.get("/health").headers.items()}
    assert "x-correlation-id" in headers


def test_openapi_generated(client: TestClient) -> None:
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"]


def test_whoami_requires_auth(client: TestClient) -> None:
    assert client.get("/whoami").status_code == 401


def test_whoami_with_token() -> None:
    sdk = create_sdk()
    api_client = TestClient(create_app(sdk))
    pair = sdk.authentication.login(Identity(subject="u1", roles=["admin"]))
    response = api_client.get("/whoami", headers={"Authorization": f"Bearer {pair.access_token}"})
    assert response.status_code == 200
    assert response.json()["subject"] == "u1"


def test_rate_limit_middleware() -> None:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limit=2, window_seconds=60.0)

    @app.get("/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    rate_client = TestClient(app)
    assert rate_client.get("/ping").status_code == 200
    assert rate_client.get("/ping").status_code == 200
    assert rate_client.get("/ping").status_code == 429


def test_pagination_dependency() -> None:
    pagination = get_pagination(page=2, size=10)
    assert isinstance(pagination, Pagination)
    assert pagination.offset == 10
    assert get_pagination(page=0, size=1_000_000).size <= 500
