import logging
from datetime import datetime, timezone

from legacy_ecms.core.uko import (
    ExtractionProvenance,
    UKOMetadata,
    UKORelationship,
    UKOType,
    UniversalKnowledgeObject,
)

logger = logging.getLogger(__name__)


class EmbeddingIdentityResolver:
    """Second-stage identity resolver using embedding similarity for fuzzy matching.

    Run after the rule-based IdentityResolver to catch cases it misses:
    "John Smith" vs "Johnathan Smith", cross-source name variations, etc.
    """

    def __init__(self, embedder: object | None = None, threshold: float = 0.85) -> None:
        self.embedder = embedder
        self.threshold = threshold

    @property
    def available(self) -> bool:
        return self.embedder is not None

    async def resolve(self, persons: list[UniversalKnowledgeObject]) -> list[UniversalKnowledgeObject]:
        """Cluster PERSON UKOs by embedding similarity and merge."""
        if not self.available or len(persons) < 2:
            return list(persons)

        names = [p.name for p in persons]
        try:
            embeddings = await self._embed_batch(names)
        except Exception as exc:
            logger.warning("Embedding resolver failed, falling back to rule-based only: %s", exc)
            return list(persons)

        if len(embeddings) != len(persons):
            return list(persons)

        clusters = self._block_and_cluster(persons, names, embeddings)
        return self._merge_clusters(clusters)

    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        if hasattr(self.embedder, "create"):
            embeddings: list[list[float]] = []
            for text in texts:
                result = self.embedder.create([text])
                if hasattr(result, "__await__"):
                    emb = await result
                else:
                    emb = result
                if isinstance(emb, list) and emb and isinstance(emb[0], (int, float)):
                    embeddings.append(emb)
                else:
                    embeddings.append(emb[0] if isinstance(emb, list) else emb)
            return embeddings
        raise RuntimeError("Embedder does not support create() method")

    def _block_and_cluster(
        self,
        persons: list[UniversalKnowledgeObject],
        names: list[str],
        embeddings: list[list[float]],
    ) -> list[list[tuple[int, UniversalKnowledgeObject, str, list[float]]]]:
        from collections import defaultdict

        blocks: dict[str, list[tuple[int, UniversalKnowledgeObject, str, list[float]]]] = defaultdict(list)
        for i, (person, name, emb) in enumerate(zip(persons, names, embeddings)):
            key = name.strip().lower()[0] if name else "_"
            blocks[key].append((i, person, name, emb))

        all_clusters: list[list[tuple[int, UniversalKnowledgeObject, str, list[float]]]] = []
        for block_items in blocks.values():
            if len(block_items) < 2:
                all_clusters.append([item] for item in block_items)
                continue

            n = len(block_items)
            uf = _UnionFind(n)
            for a in range(n):
                for b in range(a + 1, n):
                    sim = _cosine_similarity(block_items[a][3], block_items[b][3])
                    if sim >= self.threshold:
                        uf.union(a, b)

            cluster_map: dict[int, list[tuple[int, UniversalKnowledgeObject, str, list[float]]]] = defaultdict(list)
            for idx, item in enumerate(block_items):
                root = uf.find(idx)
                cluster_map[root].append(item)

            for cluster_items in cluster_map.values():
                if len(cluster_items) > 1:
                    all_clusters.append([cluster_items])
                else:
                    all_clusters.append([cluster_items])

        return all_clusters

    def _merge_clusters(
        self,
        clusters: list[list[tuple[int, UniversalKnowledgeObject, str, list[float]]]],
    ) -> list[UniversalKnowledgeObject]:
        timestamp = datetime.now(timezone.utc)
        resolved: list[UniversalKnowledgeObject] = []
        for cluster_list in clusters:
            items = cluster_list[0] if isinstance(cluster_list[0], list) else cluster_list
            if len(items) == 1:
                resolved.append(items[0][1])
                continue

            names = [item[2] for item in items]
            display_name = self._best_display_name(names)
            evidence_ids = [item[1].id for item in items]
            canonical_id = f"person:{display_name.lower().replace(' ', '-')}"
            source_person = items[0][1]

            pairs = [(a, b) for a_idx in range(len(items)) for b_idx in range(a_idx + 1, len(items))]
            mean_sim = 0.85
            if pairs:
                similarities = [
                    _cosine_similarity(items[a][3], items[b][3])
                    for a, b in zip(
                        [p[0] for p in pairs], [p[1] for p in pairs]
                    )
                ]
                mean_sim = sum(similarities) / len(similarities)

            resolved.append(
                UniversalKnowledgeObject(
                    id=canonical_id,
                    type=UKOType.PERSON,
                    name=display_name,
                    content=f"Resolved person identity for {display_name} via embedding similarity",
                    metadata=UKOMetadata(
                        source="identity",
                        source_id=canonical_id,
                        created_at=source_person.metadata.created_at,
                        modified_at=timestamp,
                        tags=["resolved-person", "embedding-resolved"],
                        tenant_id=source_person.metadata.tenant_id,
                    ),
                    relationships=[
                        UKORelationship(
                            target_id=evidence_id,
                            relationship="same_as",
                            target_type=UKOType.PERSON,
                            confidence=round(mean_sim, 4),
                            provenance=ExtractionProvenance(
                                extraction_method="embedding_resolver",
                                extraction_timestamp=timestamp,
                                confidence=round(mean_sim, 4),
                                evidence_snippet=f"embedding similarity cluster: {display_name} resolves {evidence_id}",
                                model_version="",
                                pipeline_stage="identity",
                            ),
                        )
                        for _, evidence_id in zip(items, evidence_ids)
                    ],
                    raw_data={"cluster_names": names, "mean_similarity": mean_sim},
                    provenance=ExtractionProvenance(
                        extraction_method="embedding_resolver",
                        extraction_timestamp=timestamp,
                        confidence=round(mean_sim, 4),
                        evidence_snippet=f"resolved via embeddings: {display_name} from {len(items)} names",
                        model_version="",
                        pipeline_stage="identity",
                    ),
                )
            )
        return resolved

    @staticmethod
    def _best_display_name(names: list[str]) -> str:
        return max(names, key=lambda n: (len(n.split()), len(n)))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(ai * bi for ai, bi in zip(a, b))
    norm_a = sum(ai * ai for ai in a) ** 0.5
    norm_b = sum(bi * bi for bi in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            self.parent[rx] = ry
        elif self.rank[rx] > self.rank[ry]:
            self.parent[ry] = rx
        else:
            self.parent[ry] = rx
            self.rank[rx] += 1
