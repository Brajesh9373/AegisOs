"""Backward-compat re-exports from the new domain model.

This module is maintained for existing callers. New code should import
directly from `legacy_ecms.memory.domain`.
"""

from legacy_ecms.memory.domain import (
    DEFAULT_EVIDENCE_WEIGHTS,
    Evidence,
    EvidenceSource,
    MemoryAtom,
    MemoryRelationship,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    RelatedAtom,
    RelationshipType,
)

# ── AtomStore — thin compat wrapper around FileMemoryStore ──────────

from pathlib import Path
from legacy_ecms.memory.stores.file_store import FileMemoryStore


class AtomStore:
    """Thin wrapper around FileMemoryStore for backward compat.

    New code should use FileMemoryStore directly via the MemoryStore protocol.
    """

    def __init__(self, memory_root: Path) -> None:
        self._store = FileMemoryStore(memory_root)
        self._index_path = memory_root / "memory_atoms.json"

    @property
    def _atoms(self) -> dict[str, MemoryAtom]:
        # Leaky compat — direct dict access used by old seed scripts
        return self._store._atoms

    def upsert(self, atom: MemoryAtom) -> None:
        self._store.upsert_atom(atom)

    def get(self, atom_id: str) -> MemoryAtom | None:
        return self._store.get_atom(atom_id)

    def search(self, query: str, limit: int = 5) -> list[MemoryAtom]:
        return self._store.search_atoms(query, limit)

    def search_by_topic(self, topic: str, limit: int = 8) -> list[MemoryAtom]:
        return self._store.search_by_topic(topic, limit)

    def list_all(self, limit: int = 50) -> list[MemoryAtom]:
        return self._store.list_all(limit)
