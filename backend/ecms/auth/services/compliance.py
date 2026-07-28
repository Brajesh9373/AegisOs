"""Compliance engine (SECTION 220).

Implements retention, legal hold and the right to be forgotten. A subject under
legal hold can never be deleted or forgotten; retention expiry is computed from a
creation time and a retention window.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from ecms.shared.time import utcnow

__all__ = ["ComplianceEngine"]


class ComplianceEngine:
    """Retention, legal hold and right-to-forget controls (SECTION 220)."""

    def __init__(self) -> None:
        """Initialize with no holds or forgotten subjects."""
        self._legal_holds: set[str] = set()
        self._forgotten: set[str] = set()

    def place_legal_hold(self, subject: str) -> None:
        """Place a legal hold on a subject, preventing deletion."""
        self._legal_holds.add(subject)

    def release_legal_hold(self, subject: str) -> None:
        """Release a legal hold on a subject."""
        self._legal_holds.discard(subject)

    def under_legal_hold(self, subject: str) -> bool:
        """Return whether a subject is under legal hold."""
        return subject in self._legal_holds

    def forget(self, subject: str) -> bool:
        """Honor a right-to-forget request unless the subject is under legal hold.

        Returns:
            ``True`` if the subject was forgotten, ``False`` if a legal hold blocked it.
        """
        if subject in self._legal_holds:
            return False
        self._forgotten.add(subject)
        return True

    def is_forgotten(self, subject: str) -> bool:
        """Return whether a subject has been forgotten."""
        return subject in self._forgotten

    def retention_expired(self, created_at: datetime, retention_days: int) -> bool:
        """Return whether a retention window has elapsed since ``created_at``."""
        return utcnow() >= created_at + timedelta(days=retention_days)
