"""Event-bus → WebSocket telemetry bridge for Mission Control (SECTION 195/234).

The bridge is the single fan-out point that turns the enterprise event bus into the
frontend Unified Event Pipeline (Frontend Master Prompt SECTION 422/426/440): it subscribes
to *every* event, wraps each in a :class:`TelemetryEnvelope` stamped with a monotonic
``sequence``, retains a bounded replay buffer so reconnecting clients can recover missed
events, and broadcasts to connected clients through a :class:`Broadcaster`.

Dependency direction: this module belongs to the transport layer and must not depend on the
API gateway. Broadcasters (such as the API's connection manager) are injected via a
structural :class:`Broadcaster` protocol so the gateway depends on the bridge, never the
reverse.
"""

from __future__ import annotations

from collections import deque
from typing import Protocol, runtime_checkable

from ecms.events import EventBus
from ecms.infrastructure.telemetry import get_logger
from ecms.shared.events import BaseEvent
from ecms.websocket.envelope import TelemetryEnvelope, to_envelope

__all__ = ["Broadcaster", "TelemetryBridge"]

_DEFAULT_BUFFER_SIZE = 1000


@runtime_checkable
class Broadcaster(Protocol):
    """A sink able to deliver a JSON message to connected clients.

    ``session_id`` is the owning session of the event being broadcast; implementations use
    it for session-scoped routing (workspace connections receive everything, session
    connections receive their session's events plus session-less events).
    """

    async def broadcast(
        self,
        message: dict[str, object],
        *,
        session_id: str | None = None,
    ) -> None:
        """Deliver a JSON message to connected clients, scoped by ``session_id``."""


class TelemetryBridge:
    """Fans enterprise events out to Mission Control over WebSocket (SECTION 234).

    The bridge assigns each broadcast a monotonic ``sequence`` (independent of the durable
    event-store sequence) that the frontend uses to order and deduplicate events and to
    request gap recovery after a reconnect.
    """

    def __init__(
        self,
        broadcaster: Broadcaster,
        *,
        buffer_size: int = _DEFAULT_BUFFER_SIZE,
    ) -> None:
        """Initialize the bridge.

        Args:
            broadcaster: The sink that delivers envelopes to connected clients.
            buffer_size: Maximum number of recent envelopes retained for replay.
        """
        self._broadcaster = broadcaster
        self._buffer: deque[TelemetryEnvelope] = deque(maxlen=buffer_size)
        self._sequence = 0
        self._logger = get_logger("ecms.websocket.telemetry")

    @property
    def sequence(self) -> int:
        """Return the sequence of the most recently broadcast event (0 if none)."""
        return self._sequence

    def register(self, bus: EventBus) -> str:
        """Subscribe the bridge to every event on the bus.

        Args:
            bus: The event bus to observe.

        Returns:
            The subscription id (so the bridge can be detached in tests or on shutdown).
        """
        return bus.subscribe(self._on_event)

    async def _on_event(self, event: BaseEvent) -> None:
        """Handle one event: buffer it, then broadcast it. Never raises."""
        envelope = self._record(event)
        await self._broadcaster.broadcast(
            envelope.model_dump(),
            session_id=envelope.session_id,
        )

    def _record(self, event: BaseEvent) -> TelemetryEnvelope:
        """Assign the next sequence, buffer the envelope, and return it.

        This method performs no ``await`` so, on a single event loop, sequence assignment is
        atomic even under concurrent publication.
        """
        self._sequence += 1
        envelope = to_envelope(event, self._sequence)
        self._buffer.append(envelope)
        return envelope

    def replay_since(
        self,
        sequence: int,
        *,
        session_id: str | None = None,
    ) -> list[TelemetryEnvelope]:
        """Return buffered envelopes newer than ``sequence`` for gap recovery.

        Args:
            sequence: The last sequence the client already has; only newer envelopes
                are returned.
            session_id: If given, restrict to that session's events plus session-less
                events (mirrors broadcast routing); ``None`` returns all newer events.

        Returns:
            The matching envelopes in ascending sequence order.
        """
        return [
            envelope
            for envelope in self._buffer
            if envelope.sequence > sequence
            and (
                session_id is None
                or envelope.session_id is None
                or envelope.session_id == session_id
            )
        ]
