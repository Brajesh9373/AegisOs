"""Tests for Prometheus metrics."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ecms.api.rest.metrics import _count_scan_keys, _stream_pending
from ecms.infrastructure.telemetry import MetricsRegistry


def test_observe_request_and_render() -> None:
    metrics = MetricsRegistry()
    metrics.observe_request(method="GET", path="/health", status=200, duration=0.01)
    output = metrics.render().decode("utf-8")
    assert "ecms_requests_total" in output
    assert "ecms_request_duration_seconds" in output


def test_record_error() -> None:
    metrics = MetricsRegistry()
    metrics.record_error(component="api", error_type="ValueError")
    assert "ecms_errors_total" in metrics.render().decode("utf-8")


def test_custom_counter_and_histogram() -> None:
    metrics = MetricsRegistry()
    counter = metrics.counter("custom_total", "Custom counter.", ["kind"])
    counter.labels(kind="x").inc()
    histogram = metrics.histogram("custom_seconds", "Custom histogram.")
    histogram.observe(0.5)
    output = metrics.render().decode("utf-8")
    assert "ecms_custom_total" in output
    assert "ecms_custom_seconds" in output


@pytest.mark.asyncio
async def test_stream_pending_supports_mapping_response() -> None:
    redis = AsyncMock()
    redis.xpending.return_value = {"pending": 7}

    assert await _stream_pending(redis, "partitions", "extractors") == 7


@pytest.mark.asyncio
async def test_stream_pending_is_zero_before_group_exists() -> None:
    redis = AsyncMock()
    redis.xpending.side_effect = RuntimeError("NOGROUP")

    assert await _stream_pending(redis, "partitions", "extractors") == 0


@pytest.mark.asyncio
async def test_count_scan_keys_scans_all_cursor_pages() -> None:
    redis = AsyncMock()
    redis.scan.side_effect = [(b"12", [b"a", b"b"]), (0, [b"c"])]

    count = await _count_scan_keys(redis, "worker-health:*")

    assert count == 3
    assert redis.scan.await_count == 2
