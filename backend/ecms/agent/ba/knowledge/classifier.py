"""LLM-based classifier for knowledge ingestion.

Classifies free-text input into knowledge categories, domains, and tags
using a single structured LLM call (same OpenAI client as the BA agent).
"""

from __future__ import annotations

import json
import logging

from ecms.agent.ba.knowledge.models import CATEGORIES, KnowledgeClassifyResult

logger = logging.getLogger("ecms.knowledge.classifier")

CLASSIFY_TOOL = {
    "type": "function",
    "function": {
        "name": "classify_knowledge",
        "description": "Classify a piece of knowledge into a category, domain, and tags.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": list(CATEGORIES),
                    "description": "The knowledge category.",
                },
                "domain": {
                    "type": "string",
                    "description": "The industry/domain (e.g. healthcare, fintech, migration, manufacturing). Empty string if not domain-specific.",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-5 searchable tags that capture the key topics.",
                },
                "summary": {
                    "type": "string",
                    "description": "A one-line distillation of the knowledge.",
                },
            },
            "required": ["category", "domain", "tags", "summary"],
        },
    },
}


async def classify_knowledge(text: str) -> KnowledgeClassifyResult:
    """Classify a piece of knowledge using the LLM.

    Returns a KnowledgeClassifyResult with category, domain, tags, and summary.
    Falls back to a safe default if classification fails.
    """
    from ecms.agent.ba.model import resolve_ba_model
    from openai import AsyncOpenAI

    try:
        cfg = await resolve_ba_model()
        base_url = cfg.get("base_url") or ""
        if base_url and not base_url.rstrip("/").endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        client = AsyncOpenAI(api_key=cfg["api_key"], base_url=base_url or None)
        model = cfg["model"]

        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a knowledge classifier for a Business Analyst "
                        "agent's knowledge base. Classify the given text into the "
                        "most appropriate category, domain, and tags. Be precise: "
                        "universal_pattern is for BA methodology that applies to "
                        "ALL projects; domain_pattern is for industry-specific "
                        "knowledge; anti_pattern is for red flags and mistakes; "
                        "compliance is for regulatory frameworks; correction is for "
                        "fixing a previous mistake; project_context is for specific "
                        "project intel; architecture_pattern is for technical "
                        "patterns; success_pattern is for what worked well."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Classify this knowledge:\n\n{text[:3000]}",
                },
            ],
            tools=[CLASSIFY_TOOL],
            tool_choice={"type": "function", "function": {"name": "classify_knowledge"}},
            temperature=0.0,
            max_tokens=500,
        )

        tool_calls = resp.choices[0].message.tool_calls or []
        if tool_calls:
            data = json.loads(tool_calls[0].function.arguments or "{}")
            return KnowledgeClassifyResult(**data)

    except Exception as exc:
        logger.warning("[classifier] LLM classification failed: %s", exc)

    # Fallback: safe default
    return KnowledgeClassifyResult(
        category="universal_pattern",
        domain="",
        tags=["general"],
        summary=text[:100],
    )
