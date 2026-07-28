"""Integration tests for the WebSocket telemetry gateway."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from ecms.api.app import create_app
from ecms.api.websocket.manager import ConnectionManager
from ecms.auth import Identity
from ecms.sdk import create_sdk
from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _event(event_type: str, *, session_id: str | None = None) -> BaseEvent:
    return BaseEvent(
        event_type=event_type,
        event_category=EventCategory.SYSTEM,
        producer="test",
        session_id=session_id,
        payload={"type": event_type},
    )


class _FakeWebSocket:
    def __init__(self, *, fail: bool = False) -> None:
        self.sent: list[dict[str, object]] = []
        self._fail = fail

    async def accept(self) -> None:
        return None

    async def send_json(self, message: dict[str, object]) -> None:
        if self._fail:
            raise RuntimeError("connection is dead")
        self.sent.append(message)


def test_websocket_ready_frame(client: TestClient) -> None:
    with client.websocket_connect("/ws") as websocket:
        ready = websocket.receive_json()
    assert ready["kind"] == "ready"
    assert ready["session_id"] is None
    assert ready["sequence"] >= 0


def test_websocket_ping_pong(client: TestClient) -> None:
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()  # ready
        websocket.send_json({"kind": "ping"})
        pong = websocket.receive_json()
    assert pong["kind"] == "pong"


def test_websocket_auth_rejected(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect), client.websocket_connect("/ws?token=badtoken"):
        pass


def test_websocket_auth_accepted() -> None:
    sdk = create_sdk()
    api_client = TestClient(create_app(sdk))
    pair = sdk.authentication.login(Identity(subject="u1"))
    with api_client.websocket_connect(f"/ws?token={pair.access_token}") as websocket:
        ready = websocket.receive_json()
    assert ready["kind"] == "ready"


def test_websocket_replays_buffered_events() -> None:
    sdk = create_sdk()
    app = create_app(sdk)
    api_client = TestClient(app)

    asyncio.run(sdk.events.publish(_event("Alpha")))
    asyncio.run(sdk.events.publish(_event("Beta")))

    with api_client.websocket_connect("/ws?since=0") as websocket:
        ready = websocket.receive_json()
        total = ready["sequence"]
        frames = [websocket.receive_json() for _ in range(total)]

    types = [frame["type"] for frame in frames]
    sequences = [frame["sequence"] for frame in frames]
    assert all(frame["kind"] == "event" for frame in frames)
    assert "Alpha" in types
    assert "Beta" in types
    assert sequences == sorted(sequences)


def test_websocket_replay_via_control_message() -> None:
    sdk = create_sdk()
    app = create_app(sdk)
    api_client = TestClient(app)

    asyncio.run(sdk.events.publish(_event("Alpha")))

    with api_client.websocket_connect("/ws") as websocket:
        ready = websocket.receive_json()
        total = ready["sequence"]
        websocket.send_json({"kind": "replay", "since": 0})
        frames = [websocket.receive_json() for _ in range(total)]

    assert any(frame["type"] == "Alpha" for frame in frames)


async def test_connection_manager_scoped_broadcast() -> None:
    manager = ConnectionManager()
    workspace = _FakeWebSocket()
    session_a = _FakeWebSocket()
    await manager.connect(workspace)  # type: ignore[arg-type]
    await manager.connect(session_a, session_id="a")  # type: ignore[arg-type]
    assert manager.count == 2

    await manager.broadcast({"n": 1}, session_id="a")
    await manager.broadcast({"n": 2}, session_id="b")
    await manager.broadcast({"n": 3}, session_id=None)

    # Workspace connection receives everything.
    assert workspace.sent == [{"n": 1}, {"n": 2}, {"n": 3}]
    # Session-"a" connection receives its session plus session-less messages, not "b".
    assert session_a.sent == [{"n": 1}, {"n": 3}]


async def test_connection_manager_drops_failed_connection() -> None:
    manager = ConnectionManager()
    healthy = _FakeWebSocket()
    broken = _FakeWebSocket(fail=True)
    await manager.connect(healthy)  # type: ignore[arg-type]
    await manager.connect(broken)  # type: ignore[arg-type]

    await manager.broadcast({"n": 1})

    assert healthy.sent == [{"n": 1}]
    assert manager.count == 1  # the broken connection was dropped
