"""Procedural memory — learned workflows and reusable strategies.

Layer 6 of the 8-tier memory architecture. The agent can learn procedures
from conversations and recall them later.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class ProcedureStore:
    """NDJSON-backed procedure store. Append-only.

    Each procedure is a named sequence of steps with tools used.
    """

    def __init__(self, root: Path = Path("/app/memory")) -> None:
        self._path = root / "procedures.ndjson"

    def learn(self, name: str, description: str, steps: list[str],
              tools_used: list[str] | None = None) -> str:
        """Register a new procedure. Returns procedure id."""
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        proc = {
            "id": f"proc-{slug}",
            "name": name,
            "description": description,
            "steps": steps,
            "tools_used": tools_used or [],
            "success_count": 1,
            "last_used": "",
        }
        line = json.dumps(proc, ensure_ascii=False) + "\n"
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(line)
        return proc["id"]

    def search(self, task_description: str, limit: int = 5) -> list[dict]:
        """Find procedures matching a task description."""
        query_terms = set(re.findall(r"[a-z0-9]+", task_description.lower()))
        results: list[dict] = []

        if not self._path.exists():
            return results

        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    proc = json.loads(line)
                except json.JSONDecodeError:
                    continue

                proc_text = f"{proc.get('name', '')} {proc.get('description', '')}"
                proc_terms = set(re.findall(r"[a-z0-9]+", proc_text.lower()))
                overlap = len(query_terms & proc_terms)

                if overlap >= 2:
                    results.append({
                        "id": proc.get("id", ""),
                        "name": proc.get("name", ""),
                        "description": proc.get("description", ""),
                        "steps": proc.get("steps", []),
                        "success_count": proc.get("success_count", 0),
                    })

            results.sort(key=lambda r: r["success_count"], reverse=True)
        return results[:limit]

    def list_all(self) -> list[dict]:
        """Return all known procedures."""
        results: list[dict] = []
        if not self._path.exists():
            return results
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    proc = json.loads(line)
                    results.append({
                        "id": proc.get("id", ""),
                        "name": proc.get("name", ""),
                        "description": proc.get("description", ""),
                    })
                except json.JSONDecodeError:
                    continue
        return results


# ── Singleton ──────────────────────────────────────────────────────────

_store: ProcedureStore | None = None


def get_procedure_store() -> ProcedureStore:
    global _store
    if _store is None:
        _store = ProcedureStore()
    return _store
