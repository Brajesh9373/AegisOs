"""Telegram bot authentication — chat ID whitelist.

Only the manager's chat ID (from TELEGRAM_MANAGER_CHAT_ID env var) is allowed
to interact with the bot. Unauthorized messages are silently ignored.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("ecms.telegram.auth")

# Cached authorized chat IDs.
_authorized_ids: set[int] | None = None


def _load_authorized_ids() -> set[int]:
    """Load authorized chat IDs from environment."""
    global _authorized_ids
    if _authorized_ids is not None:
        return _authorized_ids

    raw = os.environ.get("TELEGRAM_MANAGER_CHAT_ID", "")
    _authorized_ids = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            _authorized_ids.add(int(part))

    if not _authorized_ids:
        logger.warning(
            "[telegram.auth] No TELEGRAM_MANAGER_CHAT_ID set — all messages will be rejected"
        )

    return _authorized_ids


def is_authorized(chat_id: int) -> bool:
    """Check if a chat ID is authorized to use the bot."""
    return chat_id in _load_authorized_ids()
