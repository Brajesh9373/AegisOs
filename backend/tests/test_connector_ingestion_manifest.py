from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ecms.connectors.ingestion.manifest import (
    ManifestSource,
    build_manifest,
    create_manifest_entry,
    normalize_relative_path,
)


def test_manifest_is_content_addressed_order_independent_and_immutable() -> None:
    first = ManifestSource("src\\main.py", b"print('hello')\n")
    second = ManifestSource("./README.md", b"# Example\n")

    manifest = build_manifest([first, second])
    reordered = build_manifest([second, first])

    assert [entry.relative_path for entry in manifest.entries] == [
        "README.md",
        "src/main.py",
    ]
    assert [entry.extractor_type for entry in manifest.entries] == [
        "markdown",
        "python",
    ]
    assert manifest.checksum == reordered.checksum
    assert manifest.total_bytes == len(first.content) + len(second.content)
    assert len(manifest.entries[0].content_hash) == 64
    with pytest.raises(FrozenInstanceError):
        manifest.entries[0].size_bytes = 1  # type: ignore[misc]


def test_manifest_checksum_changes_with_content_or_extractor() -> None:
    original = build_manifest([ManifestSource("app.ts", b"const value = 1")])
    changed = build_manifest([ManifestSource("app.ts", b"const value = 2")])
    custom = build_manifest(
        [ManifestSource("app.ts", b"const value = 1", extractor_type="custom")]
    )

    assert original.checksum != changed.checksum
    assert original.checksum != custom.checksum


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("src\\feature\\index.ts", "src/feature/index.ts"),
        ("./src//index.ts", "src/index.ts"),
    ],
)
def test_normalize_relative_path(value: str, expected: str) -> None:
    assert normalize_relative_path(value) == expected


@pytest.mark.parametrize("value", ["", "../secret", "src/../../secret", "/root", "C:\\root"])
def test_normalize_relative_path_rejects_unsafe_paths(value: str) -> None:
    with pytest.raises(ValueError):
        normalize_relative_path(value)


def test_manifest_rejects_duplicate_normalized_paths() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        build_manifest(
            [
                ManifestSource("src/main.py", b"one"),
                ManifestSource("src\\main.py", b"two"),
            ]
        )


def test_entry_checksum_is_stable() -> None:
    source = ManifestSource("src/main.py", b"print('hello')")
    assert create_manifest_entry(source).checksum == create_manifest_entry(source).checksum
