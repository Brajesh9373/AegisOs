"""WebSocket endpoint — Mission Control telemetry channel (SECTION 105/234).

Replaces the placeholder echo endpoint with the frontend Unified Event Pipeline transport
(Frontend Master Prompt SECTION 422-440). On connect the endpoint accepts an optional
``token`` (bearer auth), an optional ``session`` scope, and an optional ``since`` replay
cursor. It emits a ``ready`` control frame, replays any missed events, then streams live
:class:`TelemetryEnvelope` frames. Clients may send ``ping`` (heartbeat) and ``replay``
(gap recovery) control messages.

Wire protocol (server → client), discriminated by ``kind``:
    ``{"kind": "ready", "sequence": int, "session_id": str | None}``
    ``{"kind": "pong", "sequence": int}``
    ``{"kind": "event", ...envelope}``  (see :class:`TelemetryEnvelope`)
"""

from __future__ import annotations

import json
from typing import cast

from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect

from ecms.api.websocket.manager import ConnectionManager
from ecms.infrastructure.telemetry import traced_span
from ecms.sdk import EcmsSDK
from ecms.shared.exceptions import AuthenticationError
from ecms.websocket import TelemetryBridge

__all__ = ["router"]

router = APIRouter(tags=["websocket"])

_POLICY_VIOLATION = 1008


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Stream live enterprise telemetry to a Mission Control client (SECTION 234)."""
    sdk = cast("EcmsSDK", websocket.app.state.sdk)
    manager = cast("ConnectionManager", websocket.app.state.ws_manager)
    bridge = cast("TelemetryBridge", websocket.app.state.ws_telemetry)

    token = websocket.query_params.get("token")
    if token is not None:
        try:
            sdk.authentication.verify(token)
        except AuthenticationError:
            await websocket.close(code=_POLICY_VIOLATION)
            return

    session_id = websocket.query_params.get("session")
    await manager.connect(websocket, session_id=session_id)
    try:
        with traced_span("ws /ws"):
            await websocket.send_json(
                {"kind": "ready", "sequence": bridge.sequence, "session_id": session_id}
            )
            since = websocket.query_params.get("since")
            if since is not None:
                await _replay(websocket, bridge, since, session_id)
            while True:
                raw = await websocket.receive_text()
                await _handle_client_message(websocket, bridge, raw, session_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def _replay(
    websocket: WebSocket,
    bridge: TelemetryBridge,
    since_raw: str,
    session_id: str | None,
) -> None:
    """Replay buffered envelopes newer than a client-supplied cursor."""
    try:
        since = int(since_raw)
    except ValueError:
        return
    for envelope in bridge.replay_since(since, session_id=session_id):
        await websocket.send_json(envelope.model_dump())


async def _handle_client_message(
    websocket: WebSocket,
    bridge: TelemetryBridge,
    raw: str,
    session_id: str | None,
) -> None:
    """Handle a client control message (``ping`` heartbeat or ``replay`` recovery)."""
    try:
        message = json.loads(raw)
    except json.JSONDecodeError:
        return
    if not isinstance(message, dict):
        return
    kind = message.get("kind")
    if kind == "ping":
        await websocket.send_json({"kind": "pong", "sequence": bridge.sequence})
    elif kind == "replay":
        since = message.get("since")
        if isinstance(since, int):
            for envelope in bridge.replay_since(since, session_id=session_id):
                await websocket.send_json(envelope.model_dump())
