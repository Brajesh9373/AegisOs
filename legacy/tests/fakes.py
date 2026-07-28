from typing import Any

from ecms.core.episode import EpisodePayload
from ecms.core.graph import BatchWriteResult


class FakeGraphClient:
    instances: list["FakeGraphClient"] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.initialized = False
        self.closed = False
        self.episodes: list[EpisodePayload] = []
        FakeGraphClient.instances.append(self)

    async def initialize(self) -> None:
        self.initialized = True

    async def add_episode(self, episode: EpisodePayload) -> BatchWriteResult:
        self.episodes.append(episode)
        return BatchWriteResult(success_count=1)

    async def add_episodes_bulk(self, episodes: list[EpisodePayload]) -> BatchWriteResult:
        self.episodes.extend(episodes)
        return BatchWriteResult(success_count=len(episodes))

    async def add_episodes_raw_batch(self, episodes: list[EpisodePayload]) -> BatchWriteResult:
        self.episodes.extend(episodes)
        return BatchWriteResult(success_count=len(episodes))

    async def search(self, query: str, num_results: int = 10) -> list:
        return []

    async def close(self) -> None:
        self.closed = True

    @classmethod
    def reset(cls) -> None:
        cls.instances = []
