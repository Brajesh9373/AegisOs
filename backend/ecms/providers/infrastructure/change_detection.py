"""Change detection engine (SECTION 123).

Tracks the checksum of every object so only changed objects are reprocessed
during incremental synchronization.
"""

from __future__ import annotations

__all__ = ["ChangeDetector"]


class ChangeDetector:
    """Detects changed objects by comparing checksums (SECTION 123)."""

    def __init__(self) -> None:
        """Initialize with no recorded checksums."""
        self._checksums: dict[str, str] = {}

    def has_changed(self, object_id: str, checksum: str) -> bool:
        """Return whether an object changed since last seen, and record the checksum."""
        previous = self._checksums.get(object_id)
        self._checksums[object_id] = checksum
        return previous != checksum

    def forget(self, object_id: str) -> None:
        """Drop the recorded checksum for an object."""
        self._checksums.pop(object_id, None)
