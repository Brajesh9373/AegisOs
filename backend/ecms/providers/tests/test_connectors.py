"""Tests for the connector runtime (SECTION 113-129)."""

from __future__ import annotations

from pathlib import Path

from ecms.events import InMemoryEventBus
from ecms.providers import (
    ChangeDetector,
    ConnectorManager,
    CredentialManager,
    FilesystemConnector,
)
from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "a.py").write_text("import os\n", encoding="utf-8")
    (root / "b.md").write_text("# doc\n", encoding="utf-8")
    return root


async def test_filesystem_connector_discovers_and_normalizes(tmp_path: Path) -> None:
    connector = FilesystemConnector(_workspace(tmp_path))
    discovered = await connector.discover()
    assert {obj.title for obj in discovered} == {"a.py", "b.md"}
    uko = connector.normalize(discovered[0], organization_id="org-1")
    assert uko.provider == "filesystem"
    assert uko.organization_id == "org-1"
    assert uko.checksum


async def test_full_sync_publishes_ukos_and_events(tmp_path: Path) -> None:
    bus = InMemoryEventBus()
    seen: list[str] = []

    async def handler(event: BaseEvent) -> None:
        seen.append(event.event_type)

    bus.subscribe(handler, category=EventCategory.PROVIDER)
    manager = ConnectorManager(event_bus=bus)
    await manager.register(FilesystemConnector(_workspace(tmp_path)))
    ukos = await manager.full_sync("filesystem", organization_id="org-1")
    assert len(ukos) == 2
    for event_type in (
        "ConnectorRegistered",
        "DiscoveryStarted",
        "DiscoveryCompleted",
        "UkoPublished",
        "SyncCompleted",
    ):
        assert event_type in seen


async def test_incremental_sync_only_returns_changes(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    manager = ConnectorManager()
    await manager.register(FilesystemConnector(root))
    first = await manager.incremental_sync("filesystem", organization_id="org-1")
    assert len(first) == 2
    second = await manager.incremental_sync("filesystem", organization_id="org-1")
    assert second == []
    (root / "a.py").write_text("import os\nimport sys\n", encoding="utf-8")
    third = await manager.incremental_sync("filesystem", organization_id="org-1")
    assert len(third) == 1


def test_change_detector() -> None:
    detector = ChangeDetector()
    assert detector.has_changed("x", "aaa") is True
    assert detector.has_changed("x", "aaa") is False
    assert detector.has_changed("x", "bbb") is True


async def test_credential_manager_lifecycle() -> None:
    manager = CredentialManager()
    await manager.store("api_key", "secret-1")
    assert await manager.get("api_key") == "secret-1"
    await manager.rotate("api_key", "secret-2")
    assert await manager.get("api_key") == "secret-2"
    await manager.revoke("api_key")
    assert await manager.get("api_key") is None
