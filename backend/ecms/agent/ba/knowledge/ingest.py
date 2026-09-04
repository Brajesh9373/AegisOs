"""Knowledge ingestion pipeline.

Takes free-text input, classifies it (LLM), chunks if needed, generates
embeddings, and stores each chunk in the knowledge_entries table.

The manager feeds knowledge via Telegram; this pipeline processes it into
searchable, embeddable entries the BA agent can retrieve at inference time.
"""

from __future__ import annotations

import logging
import re
import uuid

from ecms.agent.ba.knowledge.classifier import classify_knowledge
from ecms.agent.ba.knowledge.embeddings import generate_embedding, generate_embeddings_batch
from ecms.agent.ba.knowledge.models import KnowledgeEntry
from ecms.agent.ba.knowledge.store import create_entry

logger = logging.getLogger("ecms.knowledge.ingest")

MAX_CHUNK_SIZE = 2000  # characters


def _chunk_text(text: str, max_size: int = MAX_CHUNK_SIZE) -> list[str]:
    """Split text into chunks at paragraph/sentence boundaries."""
    text = text.strip()
    if len(text) <= max_size:
        return [text]

    chunks: list[str] = []
    # Split on double newlines first (paragraphs).
    paragraphs = re.split(r"\n\n+", text)
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # If a single paragraph exceeds max_size, split on sentences.
            if len(para) > max_size:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) + 1 <= max_size:
                        current = (current + " " + sent).strip()
                    else:
                        if current:
                            chunks.append(current)
                        current = sent
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks or [text[:max_size]]


async def ingest_text(
    text: str,
    *,
    source: str = "telegram",
    contributor: str = "",
    project_id: str | None = None,
) -> list[KnowledgeEntry]:
    """Ingest free-text knowledge into the knowledge base.

    1. Classify the input (LLM call → category, domain, tags, summary)
    2. Chunk if >2000 chars
    3. Generate embedding for each chunk
    4. Store each chunk as a knowledge entry

    Returns the list of created entries.
    """
    text = text.strip()
    if not text:
        return []

    # Step 1: Classify
    classification = await classify_knowledge(text)
    logger.info(
        "[ingest] classified: category=%s domain=%s tags=%s",
        classification.category,
        classification.domain,
        classification.tags,
    )

    # Step 2: Chunk
    chunks = _chunk_text(text)

    # Step 3: Embed
    if len(chunks) == 1:
        embedding = await generate_embedding(chunks[0])
        embeddings = [embedding]
    else:
        embeddings = await generate_embeddings_batch(chunks)

    # Step 4: Store
    parent_id = str(uuid.uuid4()) if len(chunks) > 1 else None
    entries: list[KnowledgeEntry] = []

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        entry = await create_entry(
            content=chunk,
            category=classification.category,
            domain=classification.domain,
            tags=classification.tags,
            embedding=emb,
            source=source,
            contributor=contributor,
            project_id=project_id,
            chunk_index=i,
            parent_id=parent_id,
        )
        entries.append(entry)

    logger.info(
        "[ingest] stored %d chunk(s) for category=%s", len(entries), classification.category
    )
    return entries


async def ingest_correction(
    what_was_wrong: str,
    what_is_right: str,
    *,
    source: str = "telegram",
    contributor: str = "",
    project_id: str | None = None,
) -> list[KnowledgeEntry]:
    """Ingest a correction: stores both the anti-pattern and the correct pattern.

    This creates two entries:
    1. An anti_pattern entry for what was wrong
    2. A correction entry for what is right

    The BA agent can then retrieve both — "don't do X, do Y instead."
    """
    anti_entries = await ingest_text(
        f"ANTI-PATTERN (avoid this): {what_was_wrong}",
        source=source,
        contributor=contributor,
        project_id=project_id,
    )
    correction_entries = await ingest_text(
        f"CORRECTION (do this instead): {what_is_right}",
        source=source,
        contributor=contributor,
        project_id=project_id,
    )
    return anti_entries + correction_entries
