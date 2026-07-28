from legacy_ecms.memory.brain import GBrain


class AgentTools:
    def __init__(self, brain: GBrain) -> None:
        self.brain = brain

    async def add_note(self, topic: str, content: str) -> int:
        episodes = await self.brain.write(topic, content)
        return len(episodes)

    async def search_memory(self, query: str) -> list[dict[str, str]]:
        return await self.brain.read(query)
