"""RAG retrieval for the BA agent.

Before each BA stage, retrieves relevant knowledge from the knowledge base
using hybrid search (text + semantic), then formats it as a context block
that gets injected into the BA's system prompt.

The retrieval is project-aware: it classifies the current project's domain
and tech stack, then searches for matching knowledge. Universal patterns
are always included.
"""

from __future__ import annotations

import json
import logging

from ecms.agent.ba.knowledge.embeddings import generate_embedding
from ecms.agent.ba.knowledge.models import KnowledgeSearchResult
from ecms.agent.ba.knowledge.store import hybrid_search, list_by_category

logger = logging.getLogger("ecms.knowledge.retrieval")

# How many knowledge entries to inject per prompt.
MAX_KNOWLEDGE_ENTRIES = 15


async def _extract_project_metadata(source_text: str) -> dict:
    """Quick LLM classification of the project's domain and key terms.

    This is a lightweight call — just enough to know what knowledge to retrieve.
    Returns {"domain": str, "keywords": list[str]}.
    """
    from openai import AsyncOpenAI

    from ecms.agent.ba.model import resolve_ba_model

    try:
        cfg = await resolve_ba_model()
        base_url = cfg.get("base_url") or ""
        if base_url and not base_url.rstrip("/").endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        client = AsyncOpenAI(api_key=cfg["api_key"], base_url=base_url or None)

        resp = await client.chat.completions.create(
            model=cfg["model"],
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract the project's industry/domain and 5-8 key technical "
                        "terms from the description. You MUST respond with ONLY valid JSON, no other text: "
                        '{"domain": "healthcare", "keywords": ["EHR", "FHIR", ...]}'
                    ),
                },
                {"role": "user", "content": source_text[:2000]},
            ],
            temperature=0.0,
            max_tokens=200,
        )

        content = resp.choices[0].message.content or "{}"
        return json.loads(content)

    except Exception as exc:
        logger.warning("[retrieval] metadata extraction failed: %s", exc)
        return {"domain": "", "keywords": []}


def _format_knowledge_context(results: list[KnowledgeSearchResult]) -> str:
    """Format search results into a prompt-injectable knowledge block."""
    if not results:
        return ""

    lines = ["The following knowledge from past experience is relevant to this project:\n"]
    for i, r in enumerate(results[:MAX_KNOWLEDGE_ENTRIES], 1):
        entry = r.entry
        cat_label = entry.category.replace("_", " ").title()
        domain_label = f" [{entry.domain}]" if entry.domain else ""
        lines.append(f"{i}. [{cat_label}{domain_label}] {entry.content}")

    return "\n".join(lines)


async def retrieve_for_project(
    source_text: str,
    conversation: list[dict] | None = None,
    top_k: int = 10,
) -> str:
    """Retrieve relevant knowledge for a project discovery.

    1. Extract project metadata (domain, keywords)
    2. Always include universal patterns
    3. Hybrid search for domain/keyword-matching entries
    4. Format as a context block for prompt injection

    Returns an empty string if no knowledge is found (graceful degradation).
    """
    try:
        # Step 1: Extract project metadata
        metadata = await _extract_project_metadata(source_text)
        domain = metadata.get("domain", "")
        keywords = metadata.get("keywords", [])

        # Build a search query from keywords + domain
        query_parts = keywords[:5]
        if domain:
            query_parts.insert(0, domain)
        query = " ".join(query_parts) if query_parts else source_text[:200]

        # Step 2: Generate embedding for the search query (optional — text
        # search works without it).
        query_embedding = None
        try:
            query_embedding = await generate_embedding(query)
        except Exception as exc:
            logger.warning(
                "[retrieval] embedding generation failed, using text search only: %s", exc
            )

        # Step 3: Get universal patterns (always included)
        universal = await list_by_category("universal_pattern", top_k=5)

        # Step 4: Search for domain-specific knowledge
        if query_embedding:
            domain_results = await hybrid_search(
                query,
                query_embedding,
                domain=domain if domain else None,
                top_k=top_k,
            )
            keyword_query = " ".join(keywords[:3]) if keywords else ""
            if keyword_query:
                keyword_results = await hybrid_search(
                    keyword_query,
                    query_embedding,
                    top_k=5,
                )
            else:
                keyword_results = []
        else:
            # Fallback: text-only search
            from ecms.agent.ba.knowledge.store import search_by_text

            domain_results = await search_by_text(
                query,
                domain=domain if domain else None,
                top_k=top_k,
            )
            keyword_results = []

        # Step 5: Merge and deduplicate
        seen_ids: set[str] = set()
        all_results: list[KnowledgeSearchResult] = []

        # Universal first (they always appear)
        for entry in universal:
            if entry.id not in seen_ids:
                seen_ids.add(entry.id)
                all_results.append(
                    KnowledgeSearchResult(entry=entry, score=1.0, match_type="universal")
                )

        # Domain results
        for r in domain_results:
            if r.entry.id not in seen_ids:
                seen_ids.add(r.entry.id)
                all_results.append(r)

        # Keyword results
        for r in keyword_results:
            if r.entry.id not in seen_ids:
                seen_ids.add(r.entry.id)
                all_results.append(r)

        # Step 6: Format
        context = _format_knowledge_context(all_results)
        if context:
            logger.info(
                "[retrieval] found %d knowledge entries for domain=%s",
                len(all_results),
                domain,
            )
        return context

    except Exception as exc:
        logger.warning("[retrieval] retrieval failed, proceeding without knowledge: %s", exc)
        return ""


async def retrieve_for_correction(
    project_id: str | None = None,
    domain: str = "",
) -> str:
    """Retrieve corrections relevant to the current project or domain."""
    try:
        corrections = await list_by_category("correction", top_k=5)
        anti_patterns = await list_by_category("anti_pattern", top_k=5)

        entries = corrections + anti_patterns
        if not entries:
            return ""

        lines = ["Previous corrections and anti-patterns to avoid:\n"]
        for i, entry in enumerate(entries[:10], 1):
            lines.append(f"{i}. {entry.content}")

        return "\n".join(lines)

    except Exception as exc:
        logger.warning("[retrieval] correction retrieval failed: %s", exc)
        return ""
