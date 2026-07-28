"""Unit tests for the Mission Control WebSocket telemetry bridge."""

from __future__ import annotations

from ecms.events import InMemoryEventBus
from ecms.shared.enums import EventCategory, SecurityClassification
from ecms.shared.events import BaseEvent
from ecms.websocket import TelemetryBridge


class _Recorder:
    """A broadcaster that records every (message, session_id) it receives."""

    def __init__(self) -> None:
        self.messages: list[tuple[dict[str, object], str | None]] = []

    async def broadcast(
        self,
        message: dict[str, object],
        *,
        session_id: str | None = None,
    ) -> None:
        self.messages.append((message, session_id))


def _event(
    event_type: str,
    *,
    session_id: str | None = None,
    payload: dict[str, object] | None = None,
) -> BaseEvent:
    return BaseEvent(
        event_type=event_type,
        event_category=EventCategory.SYSTEM,
        producer="test",
        session_id=session_id,
        payload=payload or {},
    )


async def test_bridge_wraps_and_broadcasts_event() -> None:
    recorder = _Recorder()
    bridge = TelemetryBridge(recorder)
    bus = InMemoryEventBus()
    bridge.register(bus)

    await bus.publish(_event("Alpha", session_id="s1", payload={"n": 1}))

    assert len(recorder.messages) == 1
    message, scope = recorder.messages[0]
    assert scope == "s1"
    assert message["kind"] == "event"
    assert message["type"] == "Alpha"
    assert message["category"] == "system"
    assert message["sequence"] == 1
    assert message["session_id"] == "s1"
    assert message["payload"] == {"n": 1}
    assert bridge.sequence == 1


async def test_bridge_assigns_monotonic_sequence() -> None:
    recorder = _Recorder()
    bridge = TelemetryBridge(recorder)
    bus = InMemoryEventBus()
    bridge.register(bus)

    await bus.publish(_event("Alpha"))
    await bus.publish(_event("Beta"))

    assert [message["sequence"] for message, _ in recorder.messages] == [1, 2]
    assert bridge.sequence == 2


async def test_replay_since_returns_newer_events() -> None:
    bridge = TelemetryBridge(_Recorder())
    bus = InMemoryEventBus()
    bridge.register(bus)

    await bus.publish(_event("Alpha"))
    await bus.publish(_event("Beta"))

    assert [e.type for e in bridge.replay_since(0)] == ["Alpha", "Beta"]
    assert [e.type for e in bridge.replay_since(1)] == ["Beta"]
    assert bridge.replay_since(2) == []


async def test_replay_since_filters_by_session() -> None:
    bridge = TelemetryBridge(_Recorder())
    bus = InMemoryEventBus()
    bridge.register(bus)

    await bus.publish(_event("GlobalEvt", session_id=None))
    await bus.publish(_event("S1Evt", session_id="s1"))
    await bus.publish(_event("S2Evt", session_id="s2"))

    scoped = [e.type for e in bridge.replay_since(0, session_id="s1")]
    assert scoped == ["GlobalEvt", "S1Evt"]
    assert "S2Evt" not in scoped


async def test_replay_buffer_is_bounded() -> None:
    bridge = TelemetryBridge(_Recorder(), buffer_size=2)
    bus = InMemoryEventBus()
    bridge.register(bus)

    await bus.publish(_event("Alpha"))
    await bus.publish(_event("Beta"))
    await bus.publish(_event("Gamma"))

    replayed = [e.type for e in bridge.replay_since(0)]
    assert replayed == ["Beta", "Gamma"]
    assert bridge.sequence == 3


async def test_envelope_maps_all_scoping_fields() -> None:
    recorder = _Recorder()
    bridge = TelemetryBridge(recorder)
    bus = InMemoryEventBus()
    bridge.register(bus)

    event = BaseEvent(
        event_type="Scoped",
        event_category=EventCategory.KNOWLEDGE,
        producer="test",
        organization_id="org1",
        workspace_id="ws1",
        project_id="proj1",
        session_id="sess1",
        task_id="task1",
        agent_id="agent1",
        correlation_id="corr1",
        causation_id="cause1",
        security_classification=SecurityClassification.CONFIDENTIAL,
        payload={"k": "v"},
    )
    await bus.publish(event)

    message, _ = recorder.messages[0]
    assert message["organization_id"] == "org1"
    assert message["workspace_id"] == "ws1"
    assert message["project_id"] == "proj1"
    assert message["task_id"] == "task1"
    assert message["agent_id"] == "agent1"
    assert message["correlation_id"] == "corr1"
    assert message["causation_id"] == "cause1"
    assert message["category"] == "knowledge"
    assert message["classification"] == "confidential"
