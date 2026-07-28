"""Integration tests for object storage."""

from __future__ import annotations

import pytest

from ecms.infrastructure.storage import InMemoryObjectStore
from ecms.shared.exceptions import NotFoundError


async def test_in_memory_object_store() -> None:
    store = InMemoryObjectStore()
    await store.put_object("a/1.txt", b"hello")
    await store.put_object("a/2.txt", b"world")
    assert await store.get_object("a/1.txt") == b"hello"
    assert await store.list_objects("a/") == ["a/1.txt", "a/2.txt"]
    await store.delete_object("a/1.txt")
    assert await store.list_objects("a/") == ["a/2.txt"]


async def test_get_missing_object_raises() -> None:
    with pytest.raises(NotFoundError):
        await InMemoryObjectStore().get_object("nope")
