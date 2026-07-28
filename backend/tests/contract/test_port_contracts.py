"""Contract tests: adapters conform to their ports (SECTION 84)."""

from __future__ import annotations

from ecms.auth import BcryptPasswordHasher, JwtTokenCodec
from ecms.auth.interfaces.service import PasswordHasher, TokenCodec
from ecms.events import EventStore, InMemoryEventBus, InMemoryEventStore
from ecms.infrastructure.cache import Cache, InMemoryCache
from ecms.infrastructure.secrets import EnvSecretsProvider, SecretsProvider
from ecms.infrastructure.storage import InMemoryObjectStore, ObjectStore
from ecms.plugins import BasePlugin, Plugin, PluginManifest
from ecms.shared.interfaces import EventPublisher

_TEST_SECRET = "contract-test-signing-secret-0123456789"


def test_event_store_contract() -> None:
    assert isinstance(InMemoryEventStore(), EventStore)


def test_event_publisher_contract() -> None:
    assert isinstance(InMemoryEventBus(), EventPublisher)


def test_cache_contract() -> None:
    assert isinstance(InMemoryCache(), Cache)


def test_object_store_contract() -> None:
    assert isinstance(InMemoryObjectStore(), ObjectStore)


def test_password_hasher_contract() -> None:
    assert isinstance(BcryptPasswordHasher(), PasswordHasher)


def test_token_codec_contract() -> None:
    assert isinstance(JwtTokenCodec(secret=_TEST_SECRET), TokenCodec)


def test_secrets_provider_contract() -> None:
    assert isinstance(EnvSecretsProvider(), SecretsProvider)


def test_plugin_contract() -> None:
    class _SamplePlugin(BasePlugin):
        @property
        def manifest(self) -> PluginManifest:
            return PluginManifest(name="p", version="1.0.0")

    assert isinstance(_SamplePlugin(), Plugin)
