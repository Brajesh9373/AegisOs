"""Telegram bot message handlers.

Handles commands (/teach, /learn, /correct, /search, /stats) and free-form
messages (auto-classified and ingested as knowledge).
"""

from __future__ import annotations

import logging

logger = logging.getLogger("ecms.telegram.handlers")


async def handle_start(update, context) -> None:
    """Welcome message explaining what the bot does."""
    await update.message.reply_text(
        "🧠 *Knowledge Agent* — I'm the BA agent's memory.\n\n"
        "Feed me knowledge throughout the day and I'll make the BA agent "
        "smarter for every project discovery.\n\n"
        "*Commands:*\n"
        "/teach <knowledge> — teach me a pattern or best practice\n"
        "/learn <lesson> — record a lesson learned\n"
        "/correct <wrong> → <right> — correct a mistake\n"
        "/search <query> — search the knowledge base\n"
        "/stats — show knowledge base statistics\n\n"
        "*Or just talk to me naturally:*\n"
        "\"For financial services, always probe SOX compliance\"\n"
        "\"This client's CTO is very technical, skip basics\"\n\n"
        "I'll auto-classify and store everything you say.",
        parse_mode="Markdown",
    )


async def handle_teach(update, context) -> None:
    """Explicitly ingest as a pattern or best practice."""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /teach <knowledge>\nExample: /teach Always ask about data residency for EU clients")
        return

    await _ingest_and_reply(update, text, source="telegram_teach")


async def handle_learn(update, context) -> None:
    """Record a lesson learned."""
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text("Usage: /learn <lesson>\nExample: /learn Projects that skip rollback planning always fail cutover")
        return

    await _ingest_and_reply(update, f"LESSON LEARNED: {text}", source="telegram_learn")


async def handle_correct(update, context) -> None:
    """Correct a mistake: /correct <wrong> → <right>."""
    raw = " ".join(context.args) if context.args else ""
    if not raw:
        await update.message.reply_text(
            "Usage: /correct <what was wrong> → <what is right>\n"
            "Example: /correct Accepted 'real-time' without probing → "
            "Always drill into latency, conflict resolution, failure behavior"
        )
        return

    # Split on → or ->
    parts = None
    for sep in ["→", "->", "=>"]:
        if sep in raw:
            parts = raw.split(sep, 1)
            break

    if not parts or len(parts) < 2:
        await update.message.reply_text("Please use → to separate wrong from right.\nExample: /correct Accepted vague answer → Always drill into specifics")
        return

    from ecms.agent.ba.knowledge.ingest import ingest_correction
    from ecms.telegram.auth import is_authorized

    wrong = parts[0].strip()
    right = parts[1].strip()
    chat_id = update.message.chat_id

    await update.message.reply_text("⏳ Classifying and storing correction...")

    try:
        entries = await ingest_correction(
            wrong, right,
            source="telegram",
            contributor=str(chat_id),
        )
        await update.message.reply_text(
            f"✅ Correction stored ({len(entries)} entries):\n"
            f"❌ Wrong: {wrong}\n"
            f"✅ Right: {right}"
        )
    except Exception as exc:
        logger.error("[handlers] correction ingest failed: %s", exc)
        await update.message.reply_text(f"❌ Failed to store correction: {exc}")


async def handle_search(update, context) -> None:
    """Search the knowledge base."""
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text("Usage: /search <query>\nExample: /search migration rollback")
        return

    from ecms.agent.ba.knowledge.store import search_by_text

    await update.message.reply_text("🔍 Searching...")

    try:
        results = await search_by_text(query, top_k=5)
        if not results:
            await update.message.reply_text("No matching knowledge found.")
            return

        lines = [f"🔍 *Results for \"{query}\":*\n"]
        for i, r in enumerate(results, 1):
            cat = r.entry.category.replace("_", " ").title()
            domain = f" [{r.entry.domain}]" if r.entry.domain else ""
            content = r.entry.content[:150] + ("..." if len(r.entry.content) > 150 else "")
            lines.append(f"{i}. [{cat}{domain}] {content}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as exc:
        logger.error("[handlers] search failed: %s", exc)
        await update.message.reply_text(f"❌ Search failed: {exc}")


async def handle_stats(update, context) -> None:
    """Show knowledge base statistics."""
    from ecms.agent.ba.knowledge.store import get_stats

    try:
        stats = await get_stats()
        total = stats["total"]
        by_cat = stats.get("by_category", {})
        by_domain = stats.get("by_domain", {})

        lines = [f"📊 *Knowledge Base Stats*\n", f"Total entries: *{total}*\n"]

        if by_cat:
            lines.append("*By category:*")
            for cat, cnt in by_cat.items():
                lines.append(f"  • {cat.replace('_', ' ').title()}: {cnt}")

        if by_domain:
            lines.append("\n*By domain:*")
            for dom, cnt in by_domain.items():
                lines.append(f"  • {dom}: {cnt}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as exc:
        logger.error("[handlers] stats failed: %s", exc)
        await update.message.reply_text(f"❌ Failed to get stats: {exc}")


async def handle_free_form(update, context) -> None:
    """Auto-classify and ingest any non-command message as knowledge.

    This is the "casual feed" mode — the manager just talks naturally about
    what the BA should know, and the bot classifies and stores it.
    """
    text = update.message.text.strip()
    if not text:
        return

    await _ingest_and_reply(update, text, source="telegram")


async def _ingest_and_reply(update, text: str, source: str = "telegram") -> None:
    """Shared ingestion logic: classify, embed, store, reply with confirmation."""
    from ecms.agent.ba.knowledge.ingest import ingest_text

    chat_id = update.message.chat_id
    await update.message.reply_text("⏳ Classifying and storing...")

    try:
        entries = await ingest_text(
            text,
            source=source,
            contributor=str(chat_id),
        )

        if entries:
            entry = entries[0]
            cat = entry.category.replace("_", " ").title()
            domain = f" [{entry.domain}]" if entry.domain else ""
            tags = ", ".join(entry.tags[:5]) if entry.tags else "none"
            await update.message.reply_text(
                f"✅ Stored ({len(entries)} chunk{'s' if len(entries) > 1 else ''}):\n"
                f"📁 {cat}{domain}\n"
                f"🏷️ {tags}\n"
                f"📝 {entry.content[:100]}{'...' if len(entry.content) > 100 else ''}"
            )
        else:
            await update.message.reply_text("⚠️ Nothing to store.")

    except Exception as exc:
        logger.error("[handlers] ingest failed: %s", exc)
        await update.message.reply_text(f"❌ Failed to store: {exc}")
