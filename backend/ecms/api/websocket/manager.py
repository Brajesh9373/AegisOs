"""WebSocket connection manager (SECTION 105).

Tracks active connections, supports optional session-scoped channels, and broadcasts JSON
messages resiliently — a failed send drops that connection rather than propagating, so a
single dead client can never disrupt the telemetry fan-out (Frontend Master Prompt
SECTION 423/442).
"""

from __future__ import annotations

from starlette.websockets import WebSocket

__all__ = ["ConnectionManager"]


class ConnectionManager:
    """Tracks active WebSocket connections and supports scoped broadcasting.

    Each connection has an optional ``session_id`` scope. A connection with no scope is a
    *workspace* connection and receives every event; a connection scoped to a session
    receives that session's events plus session-less (global) events.
    """

    def __init__(self) -> None:
        """Initialize an empty connection manager."""
        self._connections: dict[WebSocket, str | None] = {}

    async def connect(self, websocket: WebSocket, *, session_id: str | None = None) -> None:
        """Accept and register a WebSocket connection with an optional session scope."""
        await websocket.accept()
        self._connections[websocket] = session_id

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        self._connections.pop(websocket, None)

    async def broadcast(
        self,
        message: dict[str, object],
        *,
        session_id: str | None = None,
    ) -> None:
        """Send a JSON message to every connection whose scope matches.

        Args:
            message: The JSON-serializable message to deliver.
            session_id: The owning session of the message. Workspace connections
                (unscoped) always receive it; session-scoped connections receive it only
                when their scope matches, or when the message is session-less.
        """
        for websocket, scope in list(self._connections.items()):
            if scope is not None and session_id is not None and scope != session_id:
                continue
            await self._safe_send(websocket, message)

    async def _safe_send(self, websocket: WebSocket, message: dict[str, object]) -> None:
        """Send a message, dropping the connection on any failure."""
        try:
            await websocket.send_json(message)
        except Exception:  # a dead client must not disrupt the telemetry fan-out
            self.disconnect(websocket)

    @property
    def count(self) -> int:
        """Return the number of active connections."""
        return len(self._connections)
