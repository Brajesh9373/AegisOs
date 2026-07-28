"""Immutable, deterministic repository ingestion manifests."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import PurePosixPath

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

_EXTRACTOR_BY_SUFFIX = {
    ".c": "c",
    ".cc": "cpp",
    ".cfg": "configuration",
    ".conf": "configuration",
    ".cpp": "cpp",
    ".cs": "dotnet",
    ".css": "stylesheet",
    ".go": "go",
    ".h": "c",
    ".hpp": "cpp",
    ".htm": "markup",
    ".html": "markup",
    ".ini": "configuration",
    ".java": "jvm",
    ".js": "javascript",
    ".json": "json",
    ".jsx": "javascript",
    ".kt": "jvm",
    ".kts": "jvm",
    ".md": "markdown",
    ".markdown": "markdown",
    ".php": "php",
    ".ps1": "shell",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".rst": "documentation",
    ".scala": "jvm",
    ".sh": "shell",
    ".sql": "sql",
    ".toml": "configuration",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".vue": "javascript",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
}


@dataclass(frozen=True, slots=True)
class ManifestSource:
    """Raw file material used to create a manifest entry."""

    relative_path: str
    content: bytes
    extractor_type: str | None = None


@dataclass(frozen=True, slots=True)
class ManifestEntry:
    """Content-addressed metadata for exactly one repository file."""

    relative_path: str
    size_bytes: int
    content_hash: str
    extractor_type: str

    def __post_init__(self) -> None:
        """Validate canonical entry invariants."""
        normalized = normalize_relative_path(self.relative_path)
        if normalized != self.relative_path:
            raise ValueError("manifest entry path must already be normalized")
        if self.size_bytes < 0:
            raise ValueError("manifest entry size cannot be negative")
        if not _SHA256_PATTERN.fullmatch(self.content_hash):
            raise ValueError("content_hash must be a lowercase SHA-256 digest")
        if not self.extractor_type or self.extractor_type.strip() != self.extractor_type:
            raise ValueError("extractor_type must be a non-empty normalized value")

    @property
    def checksum(self) -> str:
        """Return a stable checksum of this entry's canonical metadata."""
        return _checksum(self.as_dict())

    def as_dict(self) -> dict[str, str | int]:
        """Return canonical serializable entry metadata."""
        return {
            "relative_path": self.relative_path,
            "size_bytes": self.size_bytes,
            "content_hash": self.content_hash,
            "extractor_type": self.extractor_type,
        }


@dataclass(frozen=True, slots=True)
class RepositoryManifest:
    """An ordered immutable view of a repository revision."""

    entries: tuple[ManifestEntry, ...]
    checksum: str
    total_bytes: int

    def __post_init__(self) -> None:
        """Validate ordering, uniqueness, totals, and checksum."""
        paths = tuple(entry.relative_path for entry in self.entries)
        if paths != tuple(sorted(paths)):
            raise ValueError("manifest entries must be sorted by relative path")
        if len(paths) != len(set(paths)):
            raise ValueError("manifest cannot contain duplicate relative paths")
        if self.total_bytes != sum(entry.size_bytes for entry in self.entries):
            raise ValueError("manifest total_bytes does not match its entries")
        expected = manifest_checksum(self.entries)
        if self.checksum != expected:
            raise ValueError("manifest checksum does not match its entries")


def normalize_relative_path(path: str) -> str:
    """Normalize a repository-relative path and reject traversal or absolutes."""
    candidate = path.strip().replace("\\", "/")
    if not candidate:
        raise ValueError("relative path cannot be empty")
    if candidate.startswith("/") or re.match(r"^[A-Za-z]:", candidate):
        raise ValueError("repository paths must be relative")
    parts = [part for part in candidate.split("/") if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        raise ValueError("repository path cannot contain traversal")
    return PurePosixPath(*parts).as_posix()


def infer_extractor_type(relative_path: str) -> str:
    """Select a stable extractor family from a normalized file suffix."""
    normalized = normalize_relative_path(relative_path)
    suffix = PurePosixPath(normalized).suffix.lower()
    return _EXTRACTOR_BY_SUFFIX.get(suffix, "text")


def create_manifest_entry(source: ManifestSource) -> ManifestEntry:
    """Create immutable content-addressed metadata for a source file."""
    path = normalize_relative_path(source.relative_path)
    extractor_type = source.extractor_type or infer_extractor_type(path)
    extractor_type = extractor_type.strip().lower()
    return ManifestEntry(
        relative_path=path,
        size_bytes=len(source.content),
        content_hash=hashlib.sha256(source.content).hexdigest(),
        extractor_type=extractor_type,
    )


def build_manifest(sources: Iterable[ManifestSource]) -> RepositoryManifest:
    """Build a deterministic manifest independent of discovery order."""
    entries = tuple(
        sorted(
            (create_manifest_entry(source) for source in sources),
            key=lambda entry: entry.relative_path,
        )
    )
    paths = [entry.relative_path for entry in entries]
    if len(paths) != len(set(paths)):
        raise ValueError("manifest sources normalize to duplicate relative paths")
    return RepositoryManifest(
        entries=entries,
        checksum=manifest_checksum(entries),
        total_bytes=sum(entry.size_bytes for entry in entries),
    )


def manifest_checksum(entries: Iterable[ManifestEntry]) -> str:
    """Hash canonical entry metadata in path order."""
    ordered = sorted(entries, key=lambda entry: entry.relative_path)
    return _checksum([entry.as_dict() for entry in ordered])


def _checksum(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
