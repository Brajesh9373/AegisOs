import pytest
from fastapi.testclient import TestClient

from ecms.config import get_settings
from ecms.core.tasks.rate_limit import RateLimiter
from ecms.core.tasks.retry import RetryPolicy, retry_async
from ecms.main import create_app


def test_metrics_endpoint_records_requests() -> None:
    get_settings.cache_clear()
    client = TestClient(create_app())

    assert client.get("/health").status_code == 200
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.json()["request_count"]["/health"] >= 1


def test_api_key_middleware_can_protect_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ECMS_AUTH_ENABLED", "true")
    monkeypatch.setenv("ECMS_API_KEY", "secret")
    get_settings.cache_clear()
    client = TestClient(create_app())

    assert client.get("/health").status_code == 200
    assert client.get("/providers").status_code == 401
    assert client.get("/providers", headers={"x-api-key": "secret"}).status_code == 200

    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_retry_async_retries_until_success() -> None:
    attempts = {"count": 0}

    async def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("try again")
        return "ok"

    result = await retry_async(flaky, RetryPolicy(attempts=3, base_delay_seconds=0))

    assert result == "ok"
    assert attempts["count"] == 2


def test_rate_limiter_blocks_after_window_capacity() -> None:
    limiter = RateLimiter(max_events=2, window_seconds=60)

    assert limiter.allow()
    assert limiter.allow()
    assert not limiter.allow()
