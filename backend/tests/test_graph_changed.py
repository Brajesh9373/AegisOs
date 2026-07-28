from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ecms.visualization import graph_changed as module


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("persisted", "success_count"),
    [(False, 1), (True, 0), (True, -1)],
)
async def test_snapshot_trigger_ignores_non_durable_or_noop_writes(
    monkeypatch: pytest.MonkeyPatch,
    persisted: bool,
    success_count: int,
) -> None:
    publish = AsyncMock()
    monkeypatch.setattr(module, "graph_changed", publish)

    accepted = await module.snapshot_after_graph_write(
        persisted=persisted,
        success_count=success_count,
        source="test",
    )

    assert accepted is False
    publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_snapshot_trigger_publishes_successful_graph_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publish = AsyncMock(return_value=True)
    monkeypatch.setattr(module, "graph_changed", publish)

    accepted = await module.snapshot_after_graph_write(
        persisted=True,
        success_count=3,
        source="git",
        revision="main:42",
    )

    assert accepted is True
    publish.assert_awaited_once_with(
        "default",
        source="git",
        revision="main:42",
    )


@pytest.mark.asyncio
async def test_snapshot_trigger_does_not_fail_connector_when_queue_is_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publish = AsyncMock(side_effect=ConnectionError("redis unavailable"))
    monkeypatch.setattr(module, "graph_changed", publish)

    accepted = await module.snapshot_after_graph_write(
        persisted=True,
        success_count=1,
        source="mysql",
    )

    assert accepted is False
