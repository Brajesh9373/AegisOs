"""WebSocket terminal — spawns command-code via script+PTY, bridges raw I/O."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import shutil

from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect

__all__ = ["router"]
router = APIRouter(tags=["terminal"])

_CLI = os.environ.get("ECMS_CLI_BINARY", "command-code")
_DIR = os.environ.get("ECMS_WORKSPACE_DIR", "/workspace")


async def _read_all(reader, ws, kind):
    buf = b""
    while True:
        try:
            chunk = await reader.read(4096)
        except Exception:
            break
        if not chunk:
            break
        buf += chunk
        # Try to parse lines for progressive output
        while b"\n" in buf or b"\r" in buf:
            try:
                await ws.send_json({"kind": kind, "text": buf.decode("utf-8", errors="replace")})
            except Exception:
                break
            buf = b""
            await asyncio.sleep(0)
    if buf:
        try:
            await ws.send_json({"kind": kind, "text": buf.decode("utf-8", errors="replace")})
        except Exception:
            pass


@router.websocket("/ws/terminal")
async def terminal_endpoint(websocket: WebSocket) -> None:
    binary = shutil.which(_CLI)
    if binary is None:
        await websocket.close(code=1011, reason="command-code not found")
        return
    await websocket.accept()

    # Use script -qfc to give command-code a real PTY
    # stdout+stderr → single pipe, stdin → pipe
    proc = await asyncio.create_subprocess_exec(
        "script",
        "-qfc",
        binary,
        "/dev/null",
        cwd=_DIR,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env={**os.environ, "TERM": "xterm-256color", "FORCE_COLOR": "1", "COLORTERM": "truecolor"},
    )

    reader_task = asyncio.create_task(_read_all(proc.stdout, websocket, "stdout"))

    try:
        await websocket.send_json({"kind": "connected", "binary": binary, "pty": "script"})

        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(msg, dict):
                continue
            kind = msg.get("kind")
            if kind == "stdin":
                text = msg.get("text", "")
                try:
                    proc.stdin.write(text.encode())
                    await proc.stdin.drain()
                except Exception:
                    break
            elif kind == "kill":
                break
    except WebSocketDisconnect:
        pass
    finally:
        reader_task.cancel()
        with contextlib.suppress(Exception):
            proc.stdin.close()
        with contextlib.suppress(Exception):
            proc.kill()
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(proc.wait(), timeout=3)
