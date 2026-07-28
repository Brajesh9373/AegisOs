"""Seed the knowledge base with universal BA knowledge.

Run once at deployment to populate the knowledge base with curated patterns,
compliance frameworks, domain knowledge, and architectural patterns.

Usage (inside container):
    python -m ecms.knowledge.seed_knowledge

This is idempotent — entries are keyed by content hash, so re-running
skips already-seeded entries.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger("ecms.knowledge.seed")


def _content_hash(content: str) -> str:
    """Generate a deterministic ID from content for idempotent seeding."""
    return "seed-" + hashlib.sha256(content.encode()).hexdigest()[:16]


async def seed_file(
    filepath: Path,
    default_category: str,
    default_domain: str = "",
) -> int:
    """Seed entries from a JSON file. Returns count of new entries."""
    from ecms.agent.ba.knowledge.store import create_entry, get_entry

    data = json.loads(filepath.read_text(encoding="utf-8"))
    if not data:
        return 0

    # Try to generate embeddings, but proceed without them if the API doesn't
    # support it (e.g. the provider doesn't have text-embedding-3-small).
    # Text search (tsvector) still works without embeddings.
    texts = [item["content"] for item in data]
    embeddings = None
    try:
        from ecms.agent.ba.knowledge.embeddings import generate_embeddings_batch
        embeddings = await generate_embeddings_batch(texts)
        logger.info("[seed] generated %d embeddings", len(embeddings))
    except Exception as exc:
        logger.warning("[seed] embedding generation failed (proceeding without): %s", exc)

    created = 0
    for i, item in enumerate(data):
        content = item["content"]
        entry_id = _content_hash(content)
        emb = embeddings[i] if embeddings else None

        # Skip if already seeded.
        existing = await get_entry(entry_id)
        if existing:
            continue

        category = item.get("category", default_category)
        domain = item.get("domain", default_domain)
        tags = item.get("tags", [])

        await create_entry(
            content=content,
            category=category,
            domain=domain,
            tags=tags,
            embedding=emb,
            source="seed",
            contributor="system",
            entry_id=entry_id,
        )
        created += 1

    return created


async def seed_all() -> dict:
    """Seed all knowledge files. Returns counts per file."""
    seeds_dir = Path(__file__).parent / "seeds"

    files = {
        "universal_patterns.json": ("universal_pattern", ""),
        "compliance_frameworks.json": ("compliance", "compliance"),
        "domain_patterns.json": ("domain_pattern", ""),
        "architecture_patterns.json": ("architecture_pattern", ""),
    }

    results = {}
    for filename, (category, domain) in files.items():
        filepath = seeds_dir / filename
        if not filepath.exists():
            logger.warning("[seed] file not found: %s", filepath)
            results[filename] = 0
            continue

        count = await seed_file(filepath, category, domain)
        results[filename] = count
        logger.info("[seed] %s: %d new entries", filename, count)

    return results


def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    results = asyncio.run(seed_all())
    total = sum(results.values())
    print(f"\nSeeding complete: {total} new entries")
    for f, c in results.items():
        print(f"  {f}: {c}")


if __name__ == "__main__":
    main()
