"""Conversation history manager — JSON file-backed per session."""

from __future__ import annotations

import json
from pathlib import Path


class Conversation:
    """Stores LLM conversation messages for a single ECMS session.

    Persisted as /app/memory/sessions/{id}/history.json. Keeps the last
    50 messages to stay within context window limits.
    """

    MAX_MESSAGES = 50

    def __init__(self, session_id: str, root: Path = Path("/app/memory/sessions")) -> None:
        self._id = session_id
        self._dir = root / session_id
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "history.json"
        self._messages: list[dict] = []
        self._load()

    def _load(self) -> None:
        if self._file.exists():
            try:
                self._messages = json.loads(self._file.read_text())
                self._fix_orphans()
            except Exception:
                self._messages = []

    def _fix_orphans(self) -> None:
        """Remove assistant tool_calls that have no matching tool_response."""
        i = 0
        while i < len(self._messages):
            msg = self._messages[i]
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                tc_ids = {tc["id"] for tc in msg["tool_calls"]}
                found = set()
                for j in range(i + 1, len(self._messages)):
                    future = self._messages[j]
                    if future.get("role") == "tool" and future.get("tool_call_id") in tc_ids:
                        found.add(future["tool_call_id"])
                missing = tc_ids - found
                if missing:
                    del self._messages[i]
                    continue
            i += 1
        self._save()

    @staticmethod
    def _strip_orphans(messages: list[dict]) -> list[dict]:
        """Remove assistant tool_calls messages with no matching tool responses."""
        out: list[dict] = list(messages)
        i = 0
        while i < len(out):
            msg = out[i]
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                tc_ids = {tc["id"] for tc in msg["tool_calls"]}
                found = 0
                for j in range(i + 1, len(out)):
                    future = out[j]
                    if future.get("role") == "tool" and future.get("tool_call_id") in tc_ids:
                        found += 1
                if found < len(tc_ids):
                    del out[i]
                    continue
            i += 1
        return out

    def _save(self) -> None:
        self._file.write_text(json.dumps(self._messages, indent=2))

    def add(
        self,
        role: str,
        content: str | None = None,
        *,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
        name: str | None = None,
    ) -> None:
        """Add a message. Supports user, assistant, tool, and function_call roles."""
        msg: dict = {"role": role}
        if content is not None:
            msg["content"] = content
        if tool_calls:
            msg["tool_calls"] = tool_calls
        if tool_call_id:
            msg["tool_call_id"] = tool_call_id
        if name:
            msg["name"] = name
        self._messages.append(msg)
        self._trim()
        self._save()

    def _trim(self) -> None:
        if len(self._messages) <= self.MAX_MESSAGES:
            return
        # Keep first 2 + last N, but never split a tool_call/tool_response pair.
        # Walk backwards from end, greedily including full groups.
        keep: list[dict] = []
        needed_ids: set = set()
        for msg in reversed(self._messages):
            if msg["role"] == "tool" and msg.get("tool_call_id"):
                needed_ids.add(msg["tool_call_id"])
                keep.insert(0, msg)
            elif msg["role"] == "assistant" and msg.get("tool_calls"):
                tc_ids = {tc["id"] for tc in msg["tool_calls"]}
                if tc_ids & needed_ids or len(keep) < self.MAX_MESSAGES - 2:
                    keep.insert(0, msg)
            elif msg["role"] in ("user", "system"):
                keep.insert(0, msg)
            else:
                keep.insert(0, msg)
            if len(keep) >= self.MAX_MESSAGES - 2:
                break
        # Prepend first 2 messages (system + first user)
        result = self._messages[:2] + keep
        # Final cleanup: remove assistant tool_calls without matching tool responses
        result = self._strip_orphans(result)
        self._messages = list(result)

    def as_list(self) -> list[dict]:
        return list(self._messages)

    @property
    def message_count(self) -> int:
        return len(self._messages)

    @property
    def last_message(self) -> dict | None:
        return self._messages[-1] if self._messages else None
