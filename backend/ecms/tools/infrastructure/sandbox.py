"""Filesystem sandbox (SECTION 177).

Confines all filesystem access to a workspace root. Any attempt to resolve a path
outside the root is rejected, preventing path-traversal escapes.
"""

from __future__ import annotations

from pathlib import Path

from ecms.shared.exceptions import AuthorizationError

__all__ = ["WorkspaceSandbox"]


class WorkspaceSandbox:
    """Confines filesystem access to a single workspace root (SECTION 177)."""

    def __init__(self, root: Path) -> None:
        """Initialize the sandbox rooted at ``root`` (created if missing)."""
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        """Return the resolved sandbox root."""
        return self._root

    def resolve(self, relative: str) -> Path:
        """Resolve a path within the sandbox.

        Raises:
            AuthorizationError: If the resolved path escapes the sandbox root.
        """
        candidate = (self._root / relative).resolve()
        if candidate != self._root and not candidate.is_relative_to(self._root):
            raise AuthorizationError(f"path {relative!r} escapes the sandbox")
        return candidate
