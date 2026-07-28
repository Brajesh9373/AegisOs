"""Telegram bot runner for knowledge ingestion.

The manager feeds domain knowledge, patterns, corrections, and project context
via Telegram throughout the day. The bot auto-classifies and stores everything
in the knowledge base for BA agent retrieval during future discoveries.

Usage:
    python -m ecms.telegram.bot

Requires:
    TELEGRAM_BOT_TOKEN — bot token from @BotFather
    TELEGRAM_MANAGER_CHAT_ID — manager's chat ID (comma-separated for multiple)
"""

from __future__ import annotations

import logging
import os
import sys

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from ecms.telegram.handlers import (
    handle_correct,
    handle_free_form,
    handle_search,
    handle_start,
    handle_stats,
    handle_teach,
    handle_learn,
)

logger = logging.getLogger("ecms.telegram")


def _auth_filter():
    """Message filter that only allows authorized chat IDs."""
    from ecms.telegram.auth import is_authorized

    class AuthFilter(filters.BaseFilter):
        def filter(self, message):
            return is_authorized(message.chat_id)

    return AuthFilter()


def create_app():
    """Create and configure the Telegram bot application."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required")

    app = ApplicationBuilder().token(token).build()

    # Commands (only from authorized users)
    auth = _auth_filter()
    app.add_handler(CommandHandler("start", handle_start, filters=auth))
    app.add_handler(CommandHandler("teach", handle_teach, filters=auth))
    app.add_handler(CommandHandler("learn", handle_learn, filters=auth))
    app.add_handler(CommandHandler("correct", handle_correct, filters=auth))
    app.add_handler(CommandHandler("search", handle_search, filters=auth))
    app.add_handler(CommandHandler("stats", handle_stats, filters=auth))

    # Free-form messages (auto-ingest, only from authorized users)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & auth,
        handle_free_form,
    ))

    return app


def main():
    """Run the bot (polling mode)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    logger.info("[telegram] Starting knowledge ingestion bot...")
    app = create_app()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
