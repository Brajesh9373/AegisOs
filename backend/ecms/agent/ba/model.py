"""Resolve which AI model the BA agent should use.

Selection order:
  1. An ai_models row flagged is_ba_agent = 1 (set in Administration → AI Models).
  2. Fallback: the row flagged is_default = 1.
  3. Fallback: environment settings (openai_api_key / base_url / llm_model).
"""

from __future__ import annotations

import logging
import os

from ecms.persistence.database.rest_session import db_session

logger = logging.getLogger("ecms.ba.model")


def _get_settings_fallback() -> dict:
    """Get model config from environment when no DB row exists."""
    return {
        "model": os.environ.get("LLM_MODEL", os.environ.get("ECMS_LLM_MODEL", "glm-5")),
        "api_key": os.environ.get("ANTHROPIC_AUTH_TOKEN", os.environ.get("OPENAI_API_KEY", os.environ.get("ECMS_OPENAI_API_KEY", ""))),
        "base_url": os.environ.get("ANTHROPIC_BASE_URL", os.environ.get("OPENAI_BASE_URL", os.environ.get("ECMS_OPENAI_BASE_URL", ""))),
    }


async def resolve_ba_model() -> dict:
    """Return {model, api_key, base_url} for the BA agent."""
    row = None
    try:
        async with db_session() as session:
            from sqlalchemy import text
            # Prefer the BA-flagged model, else the default model.
            row = (await session.execute(text(
                "SELECT * FROM ai_models "
                "ORDER BY is_ba_agent DESC, is_default DESC, created_at DESC "
                "LIMIT 1"
            ))).first()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("[ba.model] DB lookup failed: %s", exc)

    if row is not None:
        d = {k.lower(): v for k, v in row._mapping.items()}
        model = d.get("model_id") or ""
        api_key = d.get("api_key") or ""
        base_url = d.get("base_url") or ""
        if model and api_key:
            logger.info("[ba.model] using configured model=%s (ba=%s default=%s)",
                        model, d.get("is_ba_agent"), d.get("is_default"))
            return {"model": model, "api_key": api_key, "base_url": base_url}

    # Fallback: try legacy_ecms settings, then env vars.
    try:
        from legacy_ecms.config import get_settings
        settings = get_settings()
        return {
            "model": settings.llm_model,
            "api_key": settings.openai_api_key,
            "base_url": settings.openai_base_url,
        }
    except ImportError:
        logger.info("[ba.model] legacy_ecms not available, using env vars")
        return _get_settings_fallback()
