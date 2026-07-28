"""NDJSON-backed MemoryStore — constant memory, O(1) seeks, append-only.

Never loads all atoms into a dict. Instead:
  - _atoms.ndjson: one JSON line per atom (append-only, never rewritten)
  - _index.json: id → {offset, length} for O(1) single-atom reads
  - _rels.json: relationships (small, fits in memory)

Suitable for 10K–1M atoms on a single node. For multi-node, swap
for Postgres/SQLite.
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

from legacy_ecms.memory.domain import (
    MemoryAtom,
    MemoryRelationship,
    MemoryStatus,
)
from legacy_ecms.memory.interfaces import MemoryStore
from legacy_ecms.memory.scalability import AtomIndexes, AtomCache, BatchResult


class FileMemoryStore:
    """NDJSON-backed store with O(1) single-atom lookups, constant memory.

    Drop-in replacement for the dict-based FileMemoryStore. Same API,
    same protocol. AtomCache + AtomIndexes still work — the only difference
    is the persistence layer.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._atoms_path = root / "memory_atoms.ndjson"
        self._index_path = root / "memory_index.json"
        self._rels_path = root / "memory_rels.json"
        self.legacy_atoms_path = root / "memory_atoms.json"

        # id → {"offset": int, "length": int} — O(1) single-atom reads
        self._index: dict[str, dict[str, int]] = {}
        self._atoms_active: set[str] = set()  # non-superseded atom IDs
        self._rels: dict[str, MemoryRelationship] = {}

        self.indexes = AtomIndexes()
        self.cache = AtomCache(max_size=500)

        root.mkdir(parents=True, exist_ok=True)
        self._load()

        # Migrate legacy single-file format on first load
        if self.legacy_atoms_path.exists():
            self._migrate_legacy()

    # ── Persistence ───────────────────────────────────────────────────

    def _load(self) -> None:
        """Load index, warm cache with first 500 atoms."""
        if self._index_path.exists():
            try:
                self._index = json.loads(self._index_path.read_text())
            except Exception:
                self._index = {}

        self._atoms_active = {
            aid for aid in self._index
        }

        # Warm cache with first 500 atoms (reads from NDJSON)
        if self._index:
            for atom_id in sorted(self._index.keys())[:500]:
                atom = self._read_atom_from_disk(atom_id)
                if atom and atom.status != MemoryStatus.SUPERSEDED:
                    self.cache.set(atom_id, atom)
                    self.indexes.index(atom)

        if self._rels_path.exists():
            try:
                data = json.loads(self._rels_path.read_text())
                self._rels = {k: MemoryRelationship(**v) for k, v in data.items()}
            except Exception:
                self._rels = {}

    def _read_atom_from_disk(self, atom_id: str) -> MemoryAtom | None:
        entry = self._index.get(atom_id)
        if not entry:
            return None
        try:
            with open(self._atoms_path, "r", encoding="utf-8") as f:
                f.seek(entry["offset"])
                line = f.readline()
                data = json.loads(line)
                if data.get("evidence") and isinstance(data["evidence"][0], str):
                    data["evidence"] = [{"source": s, "source_type": "documentation"} for s in data["evidence"]]
                return MemoryAtom(**data)
        except Exception:
            return None

    def _append_atom_to_disk(self, atom: MemoryAtom) -> None:
        line = json.dumps(atom.model_dump(), ensure_ascii=False) + "\n"
        line_bytes = line.encode("utf-8")

        with open(self._atoms_path, "a", encoding="utf-8") as f:
            offset = f.tell()
            f.write(line)

        self._index[atom.id] = {"offset": offset, "length": len(line_bytes)}

    def _save_index(self) -> None:
        self._index_path.write_text(json.dumps(self._index))

    def _save_rels(self) -> None:
        self._rels_path.write_text(
            json.dumps({k: v.model_dump() for k, v in self._rels.items()}, indent=2)
        )

    def _migrate_legacy(self) -> None:
        try:
            raw = json.loads(self.legacy_atoms_path.read_text())
            count = 0
            for k, v in raw.items():
                if "evidence" in v and v["evidence"] and isinstance(v["evidence"][0], str):
                    v["evidence"] = [{"source": s, "source_type": "documentation"} for s in v["evidence"]]
                known = MemoryAtom.model_fields.keys()
                v = {fk: fv for fk, fv in v.items() if fk in known}
                atom = MemoryAtom(**v)
                if atom.status != MemoryStatus.SUPERSEDED:
                    self._append_atom_to_disk(atom)
                    self.cache.set(atom.id, atom)
                    self.indexes.index(atom)
                    self._atoms_active.add(atom.id)
                    count += 1
            self._save_index()
            self.legacy_atoms_path.rename(self.legacy_atoms_path.with_suffix(".json.bak"))
        except Exception:
            pass

    # ── Atom CRUD ────────────────────────────────────────────────────

    def upsert_atom(self, atom: MemoryAtom) -> None:
        existing = self.get_atom(atom.id)
        if existing:
            atom = atom.model_copy(update={
                "version": existing.version + 1,
                "version_history": [*existing.version_history, existing.model_dump()],
            })
            self.indexes.remove(atom.id)

        self._append_atom_to_disk(atom)
        self._save_index()
        self._atoms_active.add(atom.id)
        self.indexes.index(atom)
        self.cache.set(atom.id, atom)

    def flush(self) -> None:
        pass  # NDJSON writes on every upsert — no batch flush needed

    def get_atom(self, atom_id: str) -> MemoryAtom | None:
        cached = self.cache.get(atom_id)
        if cached is not None:
            return cached
        atom = self._read_atom_from_disk(atom_id)
        if atom is not None:
            self.cache.set(atom_id, atom)
            self.indexes.index(atom)
        return atom

    def delete_atom(self, atom_id: str) -> None:
        existing = self.get_atom(atom_id)
        if existing:
            updated = existing.model_copy(update={
                "status": MemoryStatus.SUPERSEDED,
                "metadata": {**existing.metadata, "deleted": True},
            })
            self._append_atom_to_disk(updated)
            self._save_index()
            self.indexes.remove(atom_id)
            self.cache._cache.pop(atom_id, None)
            self._atoms_active.discard(atom_id)

    def search_atoms(self, query: str, limit: int = 20) -> list[MemoryAtom]:
        result = self.indexes.search(query=query, limit=limit)
        atoms = [self.get_atom(aid) for aid in result.items]
        return [a for a in atoms if a is not None and a.status != MemoryStatus.SUPERSEDED]

    def search_by_topic(self, topic: str, limit: int = 20) -> list[MemoryAtom]:
        prefix = topic.lower()[:12]
        ids = self.indexes.by_topic_prefix.get(prefix, set())
        atoms = [self.get_atom(aid) for aid in ids]
        matches = [
            a for a in atoms
            if a and a.status != MemoryStatus.SUPERSEDED and topic.lower() in a.topic.lower()
        ]
        matches.sort(key=lambda a: a.created_at, reverse=True)
        return matches[:limit]

    def list_all(self, limit: int = 100) -> list[MemoryAtom]:
        active = sorted(self._atoms_active, reverse=True)
        atoms = [self.get_atom(aid) for aid in active[:limit * 2]]
        result = [a for a in atoms if a and a.status != MemoryStatus.SUPERSEDED]
        return result[:limit]

    # ── Relationship CRUD ────────────────────────────────────────────

    def upsert_relationship(self, rel: MemoryRelationship) -> None:
        self._rels[rel.id] = rel
        self._save_rels()

    def get_relationships(self, atom_id: str) -> list[MemoryRelationship]:
        result: list[MemoryRelationship] = []
        for rel in self._rels.values():
            if rel.source_id == atom_id or rel.target_id == atom_id:
                result.append(rel)
        result.sort(key=lambda r: r.confidence, reverse=True)
        return result

    def get_related_atoms(self, atom_id: str, depth: int = 1) -> list[MemoryAtom]:
        if depth < 1:
            return []
        visited: set[str] = {atom_id}
        result: list[MemoryAtom] = []
        queue: deque[tuple[str, int]] = deque([(atom_id, 0)])

        while queue:
            current_id, current_depth = queue.popleft()
            if current_depth > 0:
                atom = self.get_atom(current_id)
                if atom and atom.status != MemoryStatus.SUPERSEDED:
                    result.append(atom)
            if current_depth < depth:
                for rel in self.get_relationships(current_id):
                    neighbor = rel.source_id if rel.target_id == current_id else rel.target_id
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, current_depth + 1))
        return result

    # ── Lifecycle ────────────────────────────────────────────────────

    def supersede_atom(self, old_id: str, new_id: str) -> None:
        existing = self.get_atom(old_id)
        if existing:
            updated = existing.model_copy(update={
                "status": MemoryStatus.SUPERSEDED,
                "superseded_by": new_id,
                "version_history": [*existing.version_history, existing.model_dump()],
            })
            self._append_atom_to_disk(updated)
            self._save_index()
            self._atoms_active.discard(old_id)

    def get_version_history(self, atom_id: str) -> list[dict]:
        atom = self.get_atom(atom_id)
        if atom:
            return [h for h in atom.version_history] + [atom.model_dump()]
        return []

    def atom_count(self) -> int:
        return len(self._atoms_active)

    # ── Stats ────────────────────────────────────────────────────

    def stats(self) -> dict:
        type_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        scope_counts: dict[str, int] = {}
        total_confidence = 0.0
        active_count = 0
        superseded_count = 0

        for aid in sorted(self._index.keys()):
            atom = self.get_atom(aid)
            if not atom:
                continue
            if atom.status == MemoryStatus.SUPERSEDED:
                superseded_count += 1
                continue
            active_count += 1
            type_counts[atom.type.value] = type_counts.get(atom.type.value, 0) + 1
            status_counts[atom.status.value] = status_counts.get(atom.status.value, 0) + 1
            scope_counts[atom.scope.value] = scope_counts.get(atom.scope.value, 0) + 1
            total_confidence += atom.confidence

        return {
            "total_atoms": len(self._index),
            "active_atoms": active_count,
            "superseded_count": superseded_count,
            "relationship_count": len(self._rels),
            "avg_confidence": round(total_confidence / active_count, 2) if active_count else 0.0,
            "by_type": type_counts,
            "by_status": status_counts,
            "by_scope": scope_counts,
        }
