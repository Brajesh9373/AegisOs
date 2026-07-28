"""CRUD and search operations for the knowledge_entries table.

Provides text search (Postgres tsvector), semantic search (Python cosine
similarity over stored embeddings), and hybrid search (combined).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from ecms.agent.ba.knowledge.models import KnowledgeEntry, KnowledgeSearchResult
from ecms.agent.ba.knowledge.embeddings import cosine_similarity

logger = logging.getLogger("ecms.knowledge.store")


def _row_to_entry(row) -> KnowledgeEntry:
    """Convert a DB row to a KnowledgeEntry."""
    m = row._mapping if hasattr(row, "_mapping") else row
    return KnowledgeEntry(
        id=m["id"],
        category=m["category"] or "",
        domain=m["domain"] or "",
        tags=m["tags"] or [],
        content=m["content"],
        embedding=m.get("embedding"),
        source=m["source"] or "telegram",
        contributor=m["contributor"] or "",
        project_id=m.get("project_id"),
        chunk_index=m.get("chunk_index") or 0,
        parent_id=m.get("parent_id"),
    )


async def create_entry(
    *,
    content: str,
    category: str,
    domain: str = "",
    tags: list[str] | None = None,
    embedding: list[float] | None = None,
    source: str = "telegram",
    contributor: str = "",
    project_id: str | None = None,
    chunk_index: int = 0,
    parent_id: str | None = None,
    entry_id: str | None = None,
) -> KnowledgeEntry:
    """Insert a knowledge entry and return it."""
    from ecms.persistence.database.rest_session import db_session
    from sqlalchemy import text

    eid = entry_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    async with db_session() as session:
        await session.execute(text(
            "INSERT INTO knowledge_entries "
            "(id, category, domain, tags, content, embedding, source, "
            " contributor, project_id, chunk_index, parent_id, created_at, updated_at) "
            "VALUES (:id, :cat, :dom, :tags, :content, :emb, :src, "
            " :contrib, :pid, :ci, :parent, :t, :t)"
        ), {
            "id": eid, "cat": category, "dom": domain,
            "tags": tags or [], "content": content,
            "emb": embedding, "src": source, "contrib": contributor,
            "pid": project_id, "ci": chunk_index, "parent": parent_id, "t": now,
        })

    return KnowledgeEntry(
        id=eid, category=category, domain=domain, tags=tags or [],
        content=content, embedding=embedding, source=source,
        contributor=contributor, project_id=project_id,
        chunk_index=chunk_index, parent_id=parent_id,
    )


async def get_entry(entry_id: str) -> Optional[KnowledgeEntry]:
    """Fetch a single entry by ID."""
    from ecms.persistence.database.rest_session import db_session
    from sqlalchemy import text

    async with db_session() as session:
        row = (await session.execute(text(
            "SELECT * FROM knowledge_entries WHERE id = :id"
        ), {"id": entry_id})).first()
    return _row_to_entry(row) if row else None


async def search_by_text(
    query: str,
    *,
    category: str | None = None,
    domain: str | None = None,
    top_k: int = 10,
) -> list[KnowledgeSearchResult]:
    """Full-text search using Postgres tsvector ranking."""
    from ecms.persistence.database.rest_session import db_session
    from sqlalchemy import text

    filters = []
    params: dict = {"q": query, "limit": top_k}
    if category:
        filters.append("category = :cat")
        params["cat"] = category
    if domain:
        filters.append("domain = :dom")
        params["dom"] = domain

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    async with db_session() as session:
        rows = (await session.execute(text(
            f"SELECT *, ts_rank(to_tsvector('english', content), "
            f"plainto_tsquery('english', :q)) AS rank "
            f"FROM knowledge_entries {where} "
            f"ORDER BY rank DESC LIMIT :limit"
        ), params)).fetchall()

    return [
        KnowledgeSearchResult(entry=_row_to_entry(r), score=r._mapping["rank"], match_type="text")
        for r in rows if r._mapping["rank"] > 0
    ]


async def search_by_embedding(
    query_embedding: list[float],
    *,
    category: str | None = None,
    domain: str | None = None,
    top_k: int = 10,
    threshold: float = 0.3,
) -> list[KnowledgeSearchResult]:
    """Semantic search: compute cosine similarity in Python over all entries."""
    from ecms.persistence.database.rest_session import db_session
    from sqlalchemy import text

    filters = ["embedding IS NOT NULL"]
    params: dict = {}
    if category:
        filters.append("category = :cat")
        params["cat"] = category
    if domain:
        filters.append("domain = :dom")
        params["dom"] = domain

    where = "WHERE " + " AND ".join(filters)

    async with db_session() as session:
        rows = (await session.execute(text(
            f"SELECT * FROM knowledge_entries {where}"
        ), params)).fetchall()

    scored: list[KnowledgeSearchResult] = []
    for r in rows:
        emb = r._mapping.get("embedding")
        if not emb:
            continue
        sim = cosine_similarity(query_embedding, emb)
        if sim >= threshold:
            scored.append(KnowledgeSearchResult(
                entry=_row_to_entry(r), score=sim, match_type="semantic"
            ))

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]


async def hybrid_search(
    query: str,
    query_embedding: list[float],
    *,
    category: str | None = None,
    domain: str | None = None,
    top_k: int = 10,
) -> list[KnowledgeSearchResult]:
    """Combined text + semantic search with deduplication and score fusion."""
    text_results = await search_by_text(query, category=category, domain=domain, top_k=top_k)
    semantic_results = await search_by_embedding(
        query_embedding, category=category, domain=domain, top_k=top_k
    )

    by_id: dict[str, KnowledgeSearchResult] = {}
    for r in text_results:
        by_id[r.entry.id] = r
    for r in semantic_results:
        existing = by_id.get(r.entry.id)
        if existing:
            by_id[r.entry.id] = KnowledgeSearchResult(
                entry=r.entry,
                score=max(existing.score, r.score) * 1.2,
                match_type="hybrid",
            )
        else:
            by_id[r.entry.id] = r

    results = sorted(by_id.values(), key=lambda x: x.score, reverse=True)
    return results[:top_k]


async def list_by_category(category: str, top_k: int = 50) -> list[KnowledgeEntry]:
    """List all entries in a category."""
    from ecms.persistence.database.rest_session import db_session
    from sqlalchemy import text

    async with db_session() as session:
        rows = (await session.execute(text(
            "SELECT * FROM knowledge_entries WHERE category = :cat "
            "ORDER BY created_at DESC LIMIT :limit"
        ), {"cat": category, "limit": top_k})).fetchall()

    return [_row_to_entry(r) for r in rows]


async def get_stats() -> dict:
    """Knowledge base statistics."""
    from ecms.persistence.database.rest_session import db_session
    from sqlalchemy import text

    async with db_session() as session:
        total = (await session.execute(text(
            "SELECT count(*) FROM knowledge_entries"
        ))).scalar() or 0

        by_cat = (await session.execute(text(
            "SELECT category, count(*) AS cnt FROM knowledge_entries "
            "GROUP BY category ORDER BY cnt DESC"
        ))).fetchall()

        by_domain = (await session.execute(text(
            "SELECT domain, count(*) AS cnt FROM knowledge_entries "
            "WHERE domain != '' GROUP BY domain ORDER BY cnt DESC LIMIT 20"
        ))).fetchall()

    return {
        "total": total,
        "by_category": {r._mapping["category"]: r._mapping["cnt"] for r in by_cat},
        "by_domain": {r._mapping["domain"]: r._mapping["cnt"] for r in by_domain},
    }


async def delete_entry(entry_id: str) -> bool:
    """Delete a knowledge entry by ID."""
    from ecms.persistence.database.rest_session import db_session
    from sqlalchemy import text

    async with db_session() as session:
        result = await session.execute(text(
            "DELETE FROM knowledge_entries WHERE id = :id"
        ), {"id": entry_id})
    return result.rowcount > 0
