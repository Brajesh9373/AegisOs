import logging
import re
from datetime import UTC, datetime
from pathlib import Path

from legacy_ecms.core.episode import EpisodePayload
from legacy_ecms.core.uko import UKOMetadata, UKOType, UniversalKnowledgeObject
from legacy_ecms.memory.long_term import LongTermMemory

logger = logging.getLogger(__name__)


class GBrain:
    """Self-wiring markdown memory layer."""

    def __init__(self, memory_root: Path, long_term: LongTermMemory | None = None) -> None:
        self.memory_root = memory_root
        self.long_term = long_term or LongTermMemory()
        self.memory_root.mkdir(parents=True, exist_ok=True)

    async def write(self, topic: str, content: str) -> list[EpisodePayload]:
        slug = self._slugify(topic)
        path = self.memory_root / f"{slug}.md"
        timestamp = datetime.now(UTC)
        body = f"# {topic}\n\n{content}\n"
        uko = UniversalKnowledgeObject(
            id=f"gbrain:note:{slug}",
            type=UKOType.DOCUMENT,
            name=topic,
            content=body,
            metadata=UKOMetadata(
                source="gbrain",
                source_id=str(path.relative_to(self.memory_root)),
                created_at=timestamp,
                modified_at=timestamp,
                tags=["memory-note"],
            ),
            raw_data={"path": str(path)},
        )
        episodes, write_result = await self.long_term.remember(uko)
        if write_result.failure_count > 0:
            logger.warning("GBrain write had %d graph failures", write_result.failure_count)
        path.write_text(body, encoding="utf-8")
        return episodes

    async def read(self, query: str) -> list[dict[str, str]]:
        query_terms = {term.lower() for term in re.findall(r"[a-zA-Z0-9]+", query)}
        matches: list[dict[str, str]] = []
        for path in sorted(self.memory_root.glob("*.md")):
            content = path.read_text(encoding="utf-8")
            content_terms = set(re.findall(r"[a-zA-Z0-9]+", content.lower()))
            if query_terms & content_terms:
                matches.append({"path": str(path), "content": content})
        return matches

    async def gap_analysis(self, domain: str) -> list[str]:
        matches = await self.read(domain)
        if matches:
            return []
        return [f"No memory notes found for {domain}"]

    async def synthesize(self, topic: str) -> str:
        matches = await self.read(topic)
        if not matches:
            return ""
        return "\n\n".join(match["content"] for match in matches)

    def _slugify(self, topic: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
        return slug or "untitled"
