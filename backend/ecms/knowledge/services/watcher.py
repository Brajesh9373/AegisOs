"""Knowledge watcher — auto-ingests workspace files and creates a code-aware KG.

Two-phase scan:
  1. Ingest ALL files → UCOs → graph nodes (builds complete UCO map)
  2. Create edges from AST relationships + regex import detection

Persists known file hashes to /workspace/.ecms_hashes.json across restarts.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

from ecms.graph.services.engine import GraphEngine
from ecms.infrastructure.telemetry import get_logger
from ecms.knowledge.interfaces.engine import KnowledgeEngine

__all__ = ["KnowledgeWatcher"]

_SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "dist", "build", ".next"}

_HASH_CACHE_PATH = "/workspace/.ecms_hashes.json"
_HASH_CACHE_STEM = ".ecms_hashes"


class KnowledgeWatcher:
    """Watches /workspace for new files and creates a connected knowledge graph."""

    _instance = None

    def __init__(
        self,
        engine: KnowledgeEngine,
        graph_engine: GraphEngine | None = None,
        root: str = "/workspace",
        *,
        organization_id: str = "default",
        session_id: str | None = None,
    ):
        self._engine = engine
        self._graph = graph_engine
        self._root = Path(root).resolve()
        self._org = organization_id
        self._session = session_id
        self._known: dict[str, str] = self._load_hashes()
        self._uco_map: dict[str, str] = {}
        self._logger = get_logger("ecms.knowledge.watcher")

    @classmethod
    def get_or_create(
        cls,
        engine: KnowledgeEngine,
        graph_engine: GraphEngine | None = None,
        root: str | Path = "/workspace",
        **kwargs: object,
    ):
        if cls._instance is None:
            cls._instance = cls(engine, graph_engine, str(root), **kwargs)
        return cls._instance

    # ── Main scan ─────────────────────────────────────────────────────

    async def scan(self) -> list[str]:
        """Two-phase scan: ingest all files first, then create all edges."""
        uco_ids: list[str] = []
        root = self._root
        if not root.exists():
            return uco_ids

        files = list(root.rglob("*"))
        changed = False
        analyses_by_rel: dict[str, object] = {}

        # ═══ Phase 1: Ingest ALL files → UCOs → graph nodes ═════════
        for path in files:
            if not self._should_scan(path):
                continue

            rel = str(path.relative_to(root))
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                self._logger.warning("read_failed", path=rel, error=str(exc))
                continue

            file_hash = hashlib.sha256(content.encode()).hexdigest()
            if self._known.get(rel) == file_hash:
                continue
            self._known[rel] = file_hash
            changed = True

            try:
                from ecms.shared.models import UniversalKnowledgeObject

                uko = UniversalKnowledgeObject(
                    provider="filesystem",
                    provider_object_type="file",
                    provider_object_id=rel,
                    organization_id=self._org,
                    title=rel,
                    raw_content=content,
                    language=path.suffix.lstrip("."),
                )
                analysis = self._engine.analyze(uko)
                ucos = await self._engine.ingest(uko)

                for uco in ucos:
                    uco_ids.append(uco.uco_id)
                    # Symbol-level lookup
                    self._uco_map[uco.display_name] = uco.uco_id
                    self._uco_map[uco.canonical_name] = uco.uco_id
                    # File-level / stem / package lookup — ONLY for the module UCO
                    if uco.ontology_type == "module":
                        self._uco_map[rel] = uco.uco_id
                        stem = Path(rel).stem
                        self._uco_map[stem] = uco.uco_id
                        # Package names for __init__.py (e.g. "events" for "ecms_code/events/__init__.py")
                        if stem == "__init__":
                            pkg = Path(rel).parent.name
                            self._uco_map[pkg] = uco.uco_id
                            # Also grandparent.name for nested packages
                            if Path(rel).parent.parent.name != "ecms_code":
                                pkg2 = Path(rel).parent.parent.name
                                self._uco_map[pkg2] = uco.uco_id

                    if self._graph is not None:
                        try:
                            await self._graph.upsert_uco(uco)
                        except Exception as exc:
                            self._logger.error("upsert_uco_failed", path=rel, error=str(exc))

                analyses_by_rel[rel] = analysis
                self._logger.info("ingested", path=rel, ucos=len(ucos))

            except Exception as exc:
                self._logger.error("ingest_failed", path=rel, error=str(exc))

        # ═══ Phase 2: Create ALL edges (UCO map is complete now) ═════
        if self._graph is not None:
            for rel, analysis in analyses_by_rel.items():
                # AST-embedded relationships (intra-file + inter-file via imports)
                for cr in analysis.relationships:
                    if cr.source.startswith("__"):
                        continue
                    source_id, target_id = self._resolve_edge_endpoints(cr, rel)
                    if source_id and target_id and source_id != target_id:
                        try:
                            await self._graph.create_relationship(
                                source=source_id,
                                target=target_id,
                                relationship_type=cr.relationship_type.value,
                                weight=0.85,
                                confidence=70,
                            )
                        except Exception:
                            pass

            # Regex-based import edges (fallback for non-AST languages)
            for path in files:
                if not self._should_scan(path):
                    continue
                rel = str(path.relative_to(root))
                source_id = self._uco_map.get(rel)
                if not source_id:
                    continue
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                for target in self._extract_imports(content):
                    target_id = self._resolve_import_target(target)
                    if target_id and target_id != source_id:
                        try:
                            await self._graph.create_relationship(
                                source=source_id,
                                target=target_id,
                                relationship_type="depends_on",
                                weight=0.6,
                                confidence=50,
                            )
                        except Exception:
                            pass

        if changed:
            await self._save_hashes()
        return uco_ids

    async def watch_forever(self, interval: float = 3.0) -> None:
        while True:
            try:
                await self.scan()
            except Exception as exc:
                self._logger.error("scan_error", error=str(exc))
            await asyncio.sleep(interval)

    # ── Helpers ───────────────────────────────────────────────────────

    def _should_scan(self, path: Path) -> bool:
        if not path.is_file():
            return False
        if ".commandcode" in str(path):
            return False
        if _HASH_CACHE_STEM in str(path):
            return False
        if any(skip in path.parts for skip in _SKIP_DIRS):
            return False
        return True

    def _resolve_edge_endpoints(self, cr: object, source_rel: str) -> tuple[str | None, str | None]:
        """Resolve source and target UCO IDs for a CodeRelationship."""
        from ecms.shared.enums import RelationshipType as RT

        if cr.relationship_type == RT.DEPENDS_ON:
            # DEPENDS_ON: source is the importing file, target is the imported module
            source_id = self._uco_map.get(source_rel)
            target_id = self._resolve_import_target(cr.target)
        else:
            # Intra-file relationships: source/target are symbol names
            source_id = self._uco_map.get(cr.source) or self._resolve_intrafile_target(
                cr.source, source_rel
            )
            target_id = self._uco_map.get(cr.target) or self._resolve_intrafile_target(
                cr.target, source_rel
            )
            if not target_id:
                target_id = self._resolve_import_target(cr.target)
        return source_id, target_id

    def _resolve_import_target(self, target: str) -> str | None:
        """Resolve a Python dotted import target to a UCO id.

        e.g. 'ecms.graph.services.engine' → resolves stem='engine' → UCO id
        """
        # Direct stem match
        parts = target.split(".")
        stem = parts[-1] if parts else target
        if stem in self._uco_map:
            return self._uco_map[stem]
        # Second-to-last for package-style imports (e.g. 'module.submodule')
        if len(parts) >= 2:
            pkg_stem = parts[-2]
            if pkg_stem in self._uco_map:
                return self._uco_map[pkg_stem]
        # Full dotted path as stem
        if target in self._uco_map:
            return self._uco_map[target]
        return None

    def _resolve_intrafile_target(self, name: str, source_rel: str) -> str | None:
        """Resolve a code entity name to its UCO id via canonical_name pattern matching.

        canonical_name is fully qualified: "file_path.ClassName.method_name".
        We search _uco_map keys that contain both the source file path and the
        target name — this handles name collisions like `__init__` across files.
        """
        source_prefix = source_rel
        name_lower = name.lower()
        # Try exact canonical_name variants
        for key in list(self._uco_map.keys()):
            if not key.startswith(source_prefix):
                continue
            key_lower = key.lower()
            if key_lower == f"{source_prefix}.{name}".lower():
                return self._uco_map[key]
            # Check suffix match: "file_path.Anything.name"
            if key_lower.endswith(f".{name_lower}"):
                return self._uco_map[key]
        # Fallback: display_name match within same file scope
        for key, val in self._uco_map.items():
            if key.startswith(source_prefix) and key.lower().endswith(f".{name_lower}"):
                return val
        return None

    @staticmethod
    def _extract_imports(content: str) -> set[str]:
        import re

        pattern = re.compile(
            r"""(?:import\s+.*?from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\)|@import\s+['\"]([^'\"]+)['\"]|link\s+rel=['\"]stylesheet['\"]\s+href=['\"]([^'\"]+)['\"]|script\s+src=['\"]([^'\"]+)['\"])"""
        )
        results: set[str] = set()
        for match in pattern.finditer(content):
            target = next((g for g in match.groups() if g), None)
            if target:
                results.add(target)
        return results

    def _load_hashes(self) -> dict[str, str]:
        try:
            cache_path = Path(_HASH_CACHE_PATH)
            if cache_path.exists():
                return json.loads(cache_path.read_text())
        except Exception:
            pass
        return {}

    async def _save_hashes(self) -> None:
        try:
            Path(_HASH_CACHE_PATH).parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(
                lambda: Path(_HASH_CACHE_PATH).write_text(json.dumps(self._known))
            )
        except Exception:
            pass
