import sys
import types
from datetime import UTC, datetime
from enum import Enum

import pytest

from ecms.config import Settings
import ecms.core.graph as graph_module
from ecms.core.episode import EpisodePayload, EpisodePayloadType
from ecms.core.graph import GraphClient
from ecms.core.uko import UKOMetadata, UKOType, UniversalKnowledgeObject


class FakeGraphiti:
    constructed_kwargs = None

    def __init__(self, **kwargs) -> None:
        FakeGraphiti.constructed_kwargs = kwargs
        self.kwargs = None

    async def build_indices_and_constraints(self) -> None:
        return None

    async def add_episode(self, **kwargs):
        self.kwargs = kwargs
        return "episode-id"


@pytest.mark.asyncio
async def test_graph_client_uses_graphiti_source_argument(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeEpisodeType(Enum):
        text = "text"
        json = "json"

    fake_nodes = types.ModuleType("graphiti_core.nodes")
    fake_nodes.EpisodeType = FakeEpisodeType
    monkeypatch.setitem(sys.modules, "graphiti_core.nodes", fake_nodes)

    graph = GraphClient(Settings())
    fake_graphiti = FakeGraphiti()
    graph._graphiti = fake_graphiti
    uko = UniversalKnowledgeObject(
        type=UKOType.DOCUMENT,
        name="note",
        metadata=UKOMetadata(
            source="test",
            source_id="note",
            created_at=datetime(2026, 7, 5, tzinfo=UTC),
            modified_at=datetime(2026, 7, 5, tzinfo=UTC),
        ),
    )
    episode = EpisodePayload(
        uko=uko,
        name="test episode",
        episode_body="body",
        episode_type=EpisodePayloadType.TEXT,
        reference_time=datetime(2026, 7, 5, tzinfo=UTC),
        source_description="test",
    )

    await graph.add_episode(episode)

    assert "source" in fake_graphiti.kwargs
    assert "episode_type" not in fake_graphiti.kwargs


@pytest.mark.asyncio
async def test_graph_client_configures_openai_compatible_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeDriver:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeLLMConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeOpenAIClient:
        def __init__(self, config):
            self.config = config

    class FakeOpenAIEmbedderConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeOpenAIEmbedder:
        def __init__(self, config):
            self.config = config

    fake_graphiti_core = types.ModuleType("graphiti_core")
    fake_graphiti_core.Graphiti = FakeGraphiti
    fake_driver = types.ModuleType("graphiti_core.driver.falkordb_driver")
    fake_driver.FalkorDriver = FakeDriver
    fake_llm_config = types.ModuleType("graphiti_core.llm_client.config")
    fake_llm_config.LLMConfig = FakeLLMConfig
    fake_openai_client = types.ModuleType("graphiti_core.llm_client.openai_client")
    fake_openai_client.OpenAIClient = FakeOpenAIClient
    fake_embedder = types.ModuleType("graphiti_core.embedder.openai")
    fake_embedder.OpenAIEmbedder = FakeOpenAIEmbedder
    fake_embedder.OpenAIEmbedderConfig = FakeOpenAIEmbedderConfig

    monkeypatch.setitem(sys.modules, "graphiti_core", fake_graphiti_core)
    monkeypatch.setitem(sys.modules, "graphiti_core.driver.falkordb_driver", fake_driver)
    monkeypatch.setitem(sys.modules, "graphiti_core.llm_client.config", fake_llm_config)
    monkeypatch.setitem(sys.modules, "graphiti_core.llm_client.openai_client", fake_openai_client)
    monkeypatch.setitem(sys.modules, "graphiti_core.embedder.openai", fake_embedder)

    graph = GraphClient(
        Settings(
            openai_api_key="secret",
            openai_base_url="https://compatible.example/v1",
            llm_model="deepseek/deepseek-v4-flash",
            embedding_model="compatible-embedding",
            embedding_dim=1536,
            graphiti_llm_client="openai",
            graphiti_embedder="openai",
            graphiti_response_format="json_object",
        )
    )

    await graph.initialize()

    kwargs = FakeGraphiti.constructed_kwargs
    assert kwargs["llm_client"].config.kwargs["base_url"] == "https://compatible.example/v1"
    assert kwargs["llm_client"].config.kwargs["model"] == "deepseek/deepseek-v4-flash"
    assert kwargs["embedder"].config.kwargs["base_url"] == "https://compatible.example/v1"
    assert kwargs["embedder"].config.kwargs["embedding_model"] == "compatible-embedding"


@pytest.mark.asyncio
async def test_graph_client_can_select_compatible_chat_and_hash_embedder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeDriver:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeLLMConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeOpenAIClient:
        def __init__(self, config):
            self.config = config

    class FakeOpenAIEmbedderConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeOpenAIEmbedder:
        def __init__(self, config):
            self.config = config

    def fake_compatible_client(config, response_format="json_object"):
        class FakeCompatibleClient:
            pass

        client = FakeCompatibleClient()
        client.config = config
        client.response_format = response_format
        return client

    def fake_hash_embedder(embedding_dim):
        class FakeHashEmbedder:
            pass

        embedder = FakeHashEmbedder()
        embedder.embedding_dim = embedding_dim
        return embedder

    fake_graphiti_core = types.ModuleType("graphiti_core")
    fake_graphiti_core.Graphiti = FakeGraphiti
    fake_driver = types.ModuleType("graphiti_core.driver.falkordb_driver")
    fake_driver.FalkorDriver = FakeDriver
    fake_llm_config = types.ModuleType("graphiti_core.llm_client.config")
    fake_llm_config.LLMConfig = FakeLLMConfig
    fake_openai_client = types.ModuleType("graphiti_core.llm_client.openai_client")
    fake_openai_client.OpenAIClient = FakeOpenAIClient
    fake_embedder = types.ModuleType("graphiti_core.embedder.openai")
    fake_embedder.OpenAIEmbedder = FakeOpenAIEmbedder
    fake_embedder.OpenAIEmbedderConfig = FakeOpenAIEmbedderConfig

    monkeypatch.setitem(sys.modules, "graphiti_core", fake_graphiti_core)
    monkeypatch.setitem(sys.modules, "graphiti_core.driver.falkordb_driver", fake_driver)
    monkeypatch.setitem(sys.modules, "graphiti_core.llm_client.config", fake_llm_config)
    monkeypatch.setitem(sys.modules, "graphiti_core.llm_client.openai_client", fake_openai_client)
    monkeypatch.setitem(sys.modules, "graphiti_core.embedder.openai", fake_embedder)
    monkeypatch.setattr(graph_module, "OpenAICompatibleChatClient", fake_compatible_client)
    monkeypatch.setattr(graph_module, "HashEmbedder", fake_hash_embedder)

    graph = GraphClient(
        Settings(
            openai_api_key="secret",
            graphiti_llm_client="openai_compatible_chat",
            graphiti_embedder="hash",
            graphiti_response_format="json_object",
            embedding_dim=256,
        )
    )

    await graph.initialize()

    kwargs = FakeGraphiti.constructed_kwargs
    assert kwargs["llm_client"].config.kwargs["api_key"] == "secret"
    assert kwargs["llm_client"].response_format == "json_object"
    assert kwargs["embedder"].embedding_dim == 256
