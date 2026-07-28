"""Seed the atom store from existing GBrain markdown notes."""
import json, sys
sys.path.insert(0, r"D:\Navadhan\kgraph\legacy\src")
from legacy_ecms.memory.atoms import AtomStore, MemoryAtom, MemoryType, MemoryStatus, MemoryScope
from pathlib import Path

store = AtomStore(Path(r"D:\Navadhan\kgraph\backend\memory_data"))
atoms = [
    MemoryAtom(id="ECOS-001", type=MemoryType.ARCHITECTURE, topic="ECOS Architecture", summary="ECOS is a knowledge graph platform. Backend: Python FastAPI (port 8000), Frontend: Next.js 15 (port 3000), Graph DB: FalkorDB, Vector DB: Qdrant. Projects are workspace-scoped.", confidence=0.95, status=MemoryStatus.VERIFIED, scope=MemoryScope.GLOBAL, evidence=["memory/system-overview.md"], tags=["ecos", "architecture", "platform"]),
    MemoryAtom(id="AUTH-001", type=MemoryType.FACT, topic="Authentication: JWT", summary="JWT access tokens expire after 1 hour. Refresh tokens extend sessions. Tokens stored in Redis.", confidence=0.92, status=MemoryStatus.VERIFIED, scope=MemoryScope.GLOBAL, evidence=["backend/ecms/auth/service.py"], tags=["auth", "jwt", "tokens"]),
    MemoryAtom(id="AUTH-002", type=MemoryType.ARCHITECTURE, topic="Authentication: Services", summary="JwtAuthenticationService handles token signing and validation. PolicyAuthorizationService enforces RBAC. Module at backend/ecms/auth.", confidence=0.90, status=MemoryStatus.VERIFIED, scope=MemoryScope.GLOBAL, evidence=["backend/ecms/auth/"], tags=["auth", "services", "jwt"]),
    MemoryAtom(id="CATCH-001", type=MemoryType.ARCHITECTURE, topic="Catchment: Architecture", summary="Catchment is a 3-layer village data management system: geography_app (spatial queries, PostGIS), REST API layer (village details/radius/filter), data layer (PostgreSQL GIS). Written in Python.", confidence=0.88, status=MemoryStatus.DRAFT, scope=MemoryScope.PROJECT, evidence=["legacy/src/legacy_ecms/"], tags=["catchment", "architecture", "python"]),
    MemoryAtom(id="CATCH-002", type=MemoryType.OBSERVATION, topic="Catchment: Source Location", summary="Catchment source code is at bitbucket.org/navadhan-acen/catchment.git, branch master. Symlinked into the workspace.", confidence=0.85, status=MemoryStatus.VERIFIED, scope=MemoryScope.PROJECT, evidence=["workspace/"], tags=["catchment", "source", "git"], validated_at="2026-07-09T10:00:00"),
    MemoryAtom(id="MEM-001", type=MemoryType.DECISION, topic="Memory: System Prompt Design", summary="ECOS uses a compact system prompt (~37 lines) defining identity, evidence hierarchy, and behavioral rules. Infrastructure details (Redis, FalkorDB, Qdrant) are excluded. Memory is injected as structured atoms with type/confidence/status/evidence fields.", confidence=0.95, status=MemoryStatus.VERIFIED, scope=MemoryScope.GLOBAL, evidence=["backend/ecms/memory/system_prompt.py"], tags=["memory", "system-prompt", "design"], validated_at="2026-07-09T10:00:00"),
    MemoryAtom(id="MEM-002", type=MemoryType.CONVENTION, topic="Memory: Evidence Hierarchy", summary="Agent ranks evidence as: 1) files inspected directly, 2) retrieved memory, 3) user statements, 4) general knowledge. Conflicts are explicitly noted.", confidence=0.95, status=MemoryStatus.VERIFIED, scope=MemoryScope.GLOBAL, evidence=["AGENTS.md"], tags=["memory", "convention", "evidence"]),
]

for a in atoms:
    store.upsert(a)
print(f"Seeded {len(atoms)} atoms into {store._index_path}")
print(json.dumps({k: v.model_dump() for k, v in store._atoms.items()}, indent=2))
