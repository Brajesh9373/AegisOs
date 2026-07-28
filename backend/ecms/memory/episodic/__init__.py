"""Episodic event store — lightweight NDJSON-backed conversation history.

Layer 5 of the 8-tier memory architecture. Stores conversations as events
(timestamped Q&A pairs with extracted facts). No LLM cost — uses keyword
extraction from ConversationExtractor results.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EventStore:
    """Append-only NDJSON event store for conversation episodes.

    Stores each conversation turn as a JSON line in /app/memory/episodes.ndjson.
    """

    def __init__(self, root: Path = Path("/app/memory")) -> None:
        self._path = root / "episodes.ndjson"
        self._index_path = root / "episodes_index.json"
        self._index: dict[str, int] = {}
        self._load_index()

    def _load_index(self) -> None:
        if self._index_path.exists():
            try:
                self._index = json.loads(self._index_path.read_text())
            except Exception:
                self._index = {}

    def _save_index(self) -> None:
        self._index_path.write_text(json.dumps(self._index))

    def record(self, session_id: str, question: str, answer: str,
               atom_ids: list[str] | None = None) -> str:
        """Record a conversation turn as an episodic event."""
        event_id = f"ep-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{len(self._index)}"
        event = {
            "id": event_id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": question[:500],
            "answer_summary": answer[:500],
            "keywords": self._extract_keywords(question),
            "atom_ids": atom_ids or [],
        }
        line = json.dumps(event, ensure_ascii=False) + "\n"
        with open(self._path, "a", encoding="utf-8") as f:
            offset = f.tell()
            f.write(line)
        self._index[event_id] = offset
        self._save_index()
        return event_id

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search past episodes by keyword match. Returns most recent first."""
        query_terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        results: list[dict] = []

        if not self._path.exists():
            return results

        # Scan from end (most recent first)
        with open(self._path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Match against question + keywords
            event_text = f"{event.get('question', '')} {' '.join(event.get('keywords', []))}"
            event_terms = set(re.findall(r"[a-z0-9]+", event_text.lower()))

            if query_terms & event_terms:
                results.append({
                    "id": event.get("id", ""),
                    "timestamp": event.get("timestamp", ""),
                    "question": event.get("question", "")[:200],
                    "answer_preview": event.get("answer_summary", "")[:200],
                })

            if len(results) >= limit:
                break

        return results

    def recent(self, limit: int = 10) -> list[dict]:
        """Get most recent episodes."""
        results: list[dict] = []
        if not self._path.exists():
            return results
        with open(self._path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines[-limit:]):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
                results.append({
                    "id": event.get("id", ""),
                    "timestamp": event.get("timestamp", ""),
                    "question": event.get("question", "")[:200],
                })
            except json.JSONDecodeError:
                continue
        return results

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract meaningful keywords from text."""
        stopwords = {"the", "a", "an", "is", "was", "are", "has", "have", "of",
                     "in", "on", "at", "to", "for", "with", "and", "or", "that",
                     "this", "it", "be", "by", "from", "as", "not", "but", "they",
                     "what", "how", "does", "can", "i", "you", "we", "me"}
        words = re.findall(r"[a-z0-9]+", text.lower())
        return list(dict.fromkeys(w for w in words if w not in stopwords and len(w) > 2))[:15]


# ── Singleton ──────────────────────────────────────────────────────────

_store: EventStore | None = None


def get_event_store() -> EventStore:
    global _store
    if _store is None:
        _store = EventStore()
    return _store
