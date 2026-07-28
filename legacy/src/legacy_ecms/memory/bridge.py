"""Production-grade memory bridge — paginated, incremental, event-driven.

Syncs FalkorDB graph + GBrain markdown into the MemoryStore atom store
asynchronously, with change detection, batch flushing, and zero-latency
incremental updates.

Principles:
  - PAGINATED: query 500 nodes at a time via SKIP/LIMIT — constant memory
  - INCREMENTAL: SHA hash per node — only sync changed nodes after first pass
  - EVENT-DRIVEN: push from provider sync / chat capture instead of polling
  - BATCH-FLUSH: write atoms in batches, single JSON flush per batch
  - ASYNC: runs in background, never blocks the API
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from legacy_ecms.memory.domain import (
    Evidence,
    EvidenceSource,
    MemoryAtom,
    MemoryRelationship,
    MemoryScope,
    MemoryStatus,
    MemoryType,
    RelationshipType,
)

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────────
BATCH_SIZE = 100  # nodes per paginated query (keep low for memory)
EDGE_BATCH_SIZE = 1000  # edges per paginated query
HASH_CACHE_PATH = "memory_bridge_hashes.json"


class UnifiedMemoryBridge:
    """Paginated, incremental memory bridge over FalkorDB + GBrain.

    Usage:
        bridge = UnifiedMemoryBridge(Path("/app/memory"))
        total = bridge.sync_all(store)  # first call: full paginated scan
        total = bridge.sync_all(store)  # second call: only changed nodes
        bridge.push_atoms(store, [atom1, atom2])  # event-driven push
    """

    def __init__(self, memory_path: Path) -> None:
        self._memory_path = memory_path
        self._hash_cache_path = memory_path / HASH_CACHE_PATH
        self._hashes: dict[str, str] = {}  # UKO id → SHA hash
        self._load_hashes()

    # ── Hash cache for change detection ─────────────────────────────

    def _load_hashes(self) -> None:
        if self._hash_cache_path.exists():
            try:
                self._hashes = json.loads(self._hash_cache_path.read_text())
            except Exception:
                self._hashes = {}

    def _save_hashes(self) -> None:
        self._hash_cache_path.write_text(json.dumps(self._hashes))

    def _hash_node(self, uko_id: str, name: str, content: str) -> str:
        """Deterministic hash for change detection."""
        raw = f"{uko_id}|{name}|{content[:200]}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _has_changed(self, uko_id: str, name: str, content: str) -> bool:
        """Check if a UKO node has changed since last sync."""
        new_hash = self._hash_node(uko_id, name, content)
        old_hash = self._hashes.get(uko_id, "")
        if new_hash != old_hash:
            self._hashes[uko_id] = new_hash
            return True
        return False

    # ── Public API ──────────────────────────────────────────────────

    def sync_all(self, atom_store: Any) -> int:
        """Full incremental sync — paginated FalkorDB + GBrain.

        First call: full scan with pagination (all nodes).
        Subsequent calls: only changed or new nodes.

        Returns count of new/changed atoms persisted.
        """
        start = time.perf_counter()
        total = 0
        total += self._sync_falkordb(atom_store)
        total += self._sync_gbrain(atom_store)
        elapsed = (time.perf_counter() - start) * 1000
        if total:
            logger.info(
                "Memory bridge: %d atoms synced in %.0fms (total: %d)",
                total, elapsed, atom_store.atom_count(),
            )
        return total

    def push_atoms(self, atom_store: Any, atoms: list[MemoryAtom]) -> int:
        """Event-driven push — ingest specific atoms immediately."""
        count = 0
        for atom in atoms:
            atom_store.upsert_atom(atom)
            count += 1
        if count:
            atom_store.flush()
        return count

    # ── FalkorDB sync (paginated + incremental) ─────────────────────

    def _sync_falkordb(self, atom_store: Any) -> int:
        """Paginated, incremental FalkorDB → MemoryAtom sync.

        Uses SKIP/LIMIT to process nodes in batches of BATCH_SIZE.
        Change detection via SHA hash — only syncs changed nodes after
        the first full pass.
        """
        try:
            import falkordb
            from legacy_ecms.config import get_settings

            settings = get_settings()
            host, port, password = (
                settings.falkordb_host,
                settings.falkordb_port,
                settings.falkordb_password or None,
            )
            db = falkordb.FalkorDB(host=host, port=port, password=password)
            g = db.select_graph(settings.falkordb_database)
        except Exception as e:
            logger.warning("FalkorDB connection failed: %s", e)
            return 0

        # Count nodes in knowledge/decision layers only (skip raw evidence)
        try:
            count_r = g.query(
                "MATCH (u:UKO) WHERE u.layer IN ['knowledge', 'decision'] RETURN count(u)"
            )
            total_nodes = int(count_r.result_set[0][0]) if hasattr(count_r, "result_set") else 0
            logger.info("FalkorDB has %d knowledge-layer UKO nodes", total_nodes)
        except Exception as e:
            logger.warning("FalkorDB count query failed: %s", e)
            return 0

        if total_nodes == 0:
            return 0

        is_first_sync = not self._hashes
        new_atoms = 0
        falkordb_map: dict[str, str] = {}
        processed = 0

        for skip in range(0, total_nodes, BATCH_SIZE):
            try:
                result = g.query(
                    "MATCH (u:UKO) WHERE u.layer IN ['knowledge', 'decision'] "
                    "RETURN u.id, u.name, u.type, u.layer, u.content, "
                    "u.source, u.source_id, u.extraction_method, u.pipeline_stage, "
                    f"u.node_confidence ORDER BY u.id SKIP {skip} LIMIT {BATCH_SIZE}"
                )
            except Exception as e:
                logger.warning("FalkorDB query at offset %d failed: %s", skip, e)
                break

            rows = result.result_set if hasattr(result, "result_set") else result
            if not rows:
                break
            logger.debug("Batch %d-%d: %d rows", skip + 1, skip + len(rows), len(rows))
            batch_atoms = 0

            for row in rows:
                uko_id = str(row[0]) if row[0] else ""
                if not uko_id:
                    continue

                name = str(row[1]) if len(row) > 1 and row[1] else uko_id
                content = str(row[4]) if len(row) > 4 and row[4] else ""

                # Incremental: skip unchanged nodes
                if not is_first_sync and not self._has_changed(uko_id, name, content):
                    processed += 1
                    continue

                # First sync or changed: convert to atom
                uko_type = str(row[2]) if len(row) > 2 and row[2] else "unknown"
                layer = str(row[3]) if len(row) > 3 and row[3] else "evidence"
                source = str(row[5]) if len(row) > 5 and row[5] else "falkordb"
                source_id = str(row[6]) if len(row) > 6 and row[6] else uko_id
                conf = (
                    float(str(row[9]))
                    if len(row) > 9 and row[9] and str(row[9]) != "None"
                    else 0.80
                )

                mtype = self._infer_memory_type(uko_type, name, content)

                atom = MemoryAtom(
                    id=f"FDB-{uko_id.replace(':', '-')[:40].upper()}",
                    type=mtype,
                    topic=name[:80],
                    summary=content[:400] if content else f"Graph node: {name}",
                    confidence=min(1.0, max(0.3, conf)),
                    status=MemoryStatus.VERIFIED if layer == "knowledge" else MemoryStatus.DRAFT,
                    scope=MemoryScope.GLOBAL,
                    evidence=[
                        Evidence(
                            source=source_id,
                            source_type=EvidenceSource.DOCUMENTATION,
                            description=f"FalkorDB node (type: {uko_type})",
                        )
                    ],
                    tags=[uko_type, layer, source, name.lower().replace(" ", "-")[:20]],
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                atom_store.upsert_atom(atom)
                falkordb_map[uko_id] = atom.id
                batch_atoms += 1
                new_atoms += 1
                processed += 1

                # Track hash for change detection
                if is_first_sync:
                    self._hashes[uko_id] = self._hash_node(uko_id, name, content)

            # Flush after each batch (every 100 nodes) to keep memory low
            if batch_atoms:
                atom_store.flush()
                self._save_hashes()
                logger.info(
                    "FalkorDB batch %d-%d/%d: %d atoms flushed",
                    skip + 1, min(skip + BATCH_SIZE, total_nodes), total_nodes, batch_atoms,
                )

        # Final hash cache save
        if is_first_sync:
            self._save_hashes()

        # ── Sync RELATES edges (also paginated) ─────────────────
        try:
            edge_count_r = g.query("MATCH ()-[r:RELATES]->() RETURN count(r)")
            total_edges = int(edge_count_r.result_set[0][0]) if hasattr(edge_count_r, "result_set") else 0

            for skip in range(0, total_edges, EDGE_BATCH_SIZE):
                try:
                    edge_result = g.query(
                        "MATCH (a:UKO)-[r:RELATES]->(b:UKO) "
                        "RETURN a.id, r.label, b.id, r.confidence, r.extraction_method "
                        f"ORDER BY a.id SKIP {skip} LIMIT {EDGE_BATCH_SIZE}"
                    )
                except Exception:
                    continue

                edge_rows = (
                    edge_result.result_set
                    if hasattr(edge_result, "result_set")
                    else edge_result
                )
                for row in edge_rows:
                    src = str(row[0]) if row[0] else ""
                    label = str(row[1]) if len(row) > 1 and row[1] else "related_to"
                    tgt = str(row[2]) if len(row) > 2 and row[2] else ""
                    conf = (
                        float(str(row[3]))
                        if len(row) > 3 and row[3] and str(row[3]) != "None"
                        else 0.70
                    )
                    src_atom = falkordb_map.get(src)
                    tgt_atom = falkordb_map.get(tgt)
                    if not src_atom or not tgt_atom:
                        continue

                    rel_type = self._map_relationship_type(label)
                    rel = MemoryRelationship(
                        id=f"FDB-REL-{src[:8]}-{tgt[:8]}".upper(),
                        source_id=src_atom,
                        target_id=tgt_atom,
                        type=rel_type,
                        confidence=min(1.0, max(0.3, conf)),
                        evidence=[f"FalkorDB RELATES: {label}"],
                    )
                    atom_store.upsert_relationship(rel)
        except Exception as e:
            logger.debug("FalkorDB edge sync skipped: %s", e)

        logger.info(
            "FalkorDB sync: %d new/changed atoms from %d total nodes (%s)",
            new_atoms, total_nodes,
            "full scan" if is_first_sync else f"incremental ({total_nodes - new_atoms} unchanged)",
        )
        return new_atoms

    # ── GBrain markdown sync ───────────────────────────────────────

    def _sync_gbrain(self, atom_store: Any) -> int:
        """Read .md files from memory directory, create atoms."""
        new_atoms = 0
        if not self._memory_path.exists():
            return 0

        for md_file in sorted(self._memory_path.glob("*.md")):
            name = md_file.stem.replace("-", " ").title()
            gbrain_id = f"gbrain:{md_file.stem}"
            atom_id = f"GB-{md_file.stem[:30].upper()}"

            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # Check if already synced and unchanged
            content_hash = self._hash_node(gbrain_id, name, content)
            if gbrain_id in self._hashes and self._hashes.get(gbrain_id) == content_hash:
                continue

            self._hashes[gbrain_id] = content_hash

            mtype = self._infer_gbrain_type(content)
            atom = MemoryAtom(
                id=atom_id,
                type=mtype,
                topic=name,
                summary=content[:500].replace("\n", " ").strip(),
                confidence=0.85,
                status=MemoryStatus.VERIFIED,
                scope=MemoryScope.WORKSPACE,
                evidence=[
                    Evidence(
                        source=str(md_file),
                        source_type=EvidenceSource.DOCUMENTATION,
                        description="GBrain memory note",
                    )
                ],
                tags=["gbrain", "memory-note", md_file.stem.lower()[:20]],
                created_at=datetime.fromtimestamp(
                    md_file.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
            )
            atom_store.upsert_atom(atom)
            new_atoms += 1

        if new_atoms:
            atom_store.flush()
            self._save_hashes()
            logger.info("GBrain sync: %d markdown notes ingested", new_atoms)

        return new_atoms

    # ── Helpers ─────────────────────────────────────────────────────

    def _infer_memory_type(self, uko_type: str, name: str, content: str) -> MemoryType:
        t = uko_type.lower()
        if t in ("function", "class", "module", "component"):
            return MemoryType.ARCHITECTURE
        if t in ("file", "document"):
            return MemoryType.OBSERVATION
        if t in ("concept", "pattern"):
            return MemoryType.CONVENTION
        if t in ("workspace", "project"):
            return MemoryType.ARCHITECTURE
        if t in ("commit", "event"):
            return MemoryType.OBSERVATION
        cl = content.lower()
        if any(w in cl for w in ["architecture", "service", "layer"]):
            return MemoryType.ARCHITECTURE
        if any(w in cl for w in ["decision", "chose"]):
            return MemoryType.DECISION
        return MemoryType.FACT

    def _infer_gbrain_type(self, content: str) -> MemoryType:
        cl = content.lower()
        if any(w in cl for w in ["architecture", "layer", "component"]):
            return MemoryType.ARCHITECTURE
        if any(w in cl for w in ["decision", "chose", "selected"]):
            return MemoryType.DECISION
        if any(w in cl for w in ["bug", "issue", "fix", "broken"]):
            return MemoryType.BUG
        if any(w in cl for w in ["limitation", "caveat", "cannot"]):
            return MemoryType.LIMITATION
        if any(w in cl for w in ["security", "vulnerability"]):
            return MemoryType.SECURITY
        return MemoryType.OBSERVATION

    def _map_relationship_type(self, label: str) -> RelationshipType:
        mapping: dict[str, RelationshipType] = {
            "depends_on": RelationshipType.DEPENDS_ON,
            "implements": RelationshipType.IMPLEMENTS,
            "belongs_to": RelationshipType.PART_OF,
            "part_of_workspace": RelationshipType.PART_OF,
            "contained_in": RelationshipType.PART_OF,
            "calls": RelationshipType.RELATED_TO,
            "uses": RelationshipType.RELATED_TO,
            "references": RelationshipType.REFERENCES,
            "derived_from": RelationshipType.DERIVED_FROM,
            "contradicts": RelationshipType.CONTRADICTS,
            "resolves": RelationshipType.RESOLVES,
            "replaces": RelationshipType.REPLACES,
            "affects": RelationshipType.AFFECTS,
        }
        return mapping.get(label.lower(), RelationshipType.RELATED_TO)
