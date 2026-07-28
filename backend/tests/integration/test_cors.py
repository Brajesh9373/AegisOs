"""Integration tests for CORS configuration on the API gateway."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ecms.api.app import create_app
from ecms.configuration import AppSettings
from ecms.sdk import create_sdk


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_cors_allows_default_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_preflight_request(client: TestClient) -> None:
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_rejects_unknown_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://evil.example.com"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_origin_configurable_via_settings() -> None:
    settings = AppSettings(cors_allow_origins="https://app.example.com, https://admin.example.com")
    sdk = create_sdk(settings)
    api_client = TestClient(create_app(sdk))

    response = api_client.get("/health", headers={"Origin": "https://admin.example.com"})
    assert response.headers["access-control-allow-origin"] == "https://admin.example.com"
