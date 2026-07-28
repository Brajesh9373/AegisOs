"""Memory storage protocol — defines the interface for atom + relationship persistence.

Storage-agnostic. Implementations: JSON file (dev), SQLite, Postgres, etc.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from legacy_ecms.memory.domain import (
    MemoryAtom,
    MemoryRelationship,
    RelatedAtom,
)


@runtime_checkable
class MemoryStore(Protocol):
    """Protocol for memory atom + relationship storage.

    All implementations must satisfy this interface. The retrieval pipeline
    and validation pipeline depend only on this protocol — never on concrete
    storage implementations.
    """

    # ── Atom CRUD ──────────────────────────────────────────────────

    def upsert_atom(self, atom: MemoryAtom) -> None:
        """Insert or update an atom by ID. Increments version on update."""
        ...

    def get_atom(self, atom_id: str) -> MemoryAtom | None:
        """Retrieve a single atom by ID."""
        ...

    def delete_atom(self, atom_id: str) -> None:
        """Soft-delete (mark superseded) — never hard-delete knowledge."""
        ...

    def search_atoms(self, query: str, limit: int = 20) -> list[MemoryAtom]:
        """Keyword search over topics, summaries, and tags."""
        ...

    def search_by_topic(self, topic: str, limit: int = 20) -> list[MemoryAtom]:
        """Return atoms matching a topic prefix."""
        ...

    def list_all(self, limit: int = 100) -> list[MemoryAtom]:
        """Return all active atoms, most recent first."""
        ...

    # ── Relationship CRUD ──────────────────────────────────────────

    def upsert_relationship(self, rel: MemoryRelationship) -> None:
        """Insert or update a relationship by ID."""
        ...

    def get_relationships(self, atom_id: str) -> list[MemoryRelationship]:
        """Return all relationships incident on an atom (both directions)."""
        ...

    def get_related_atoms(self, atom_id: str, depth: int = 1) -> list[MemoryAtom]:
        """BFS traversal: return atoms within `depth` hops of atom_id.

        Returns atoms ordered by hop distance, then by relationship confidence.
        """
        ...

    # ── Lifecycle ──────────────────────────────────────────────────

    def supersede_atom(self, old_id: str, new_id: str) -> None:
        """Mark an atom as superseded by another. Preserves version history."""
        ...

    def get_version_history(self, atom_id: str) -> list[dict]:
        """Return the version history for an atom."""
        ...

    def atom_count(self) -> int:
        """Return total count of active (non-superseded) atoms."""
        ...

    # ── Stats ──────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Return store statistics: counts by type, status, scope."""
        ...
