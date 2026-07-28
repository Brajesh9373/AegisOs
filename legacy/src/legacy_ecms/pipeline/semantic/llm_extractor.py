import re

from legacy_ecms.core.uko import UniversalKnowledgeObject
from legacy_ecms.pipeline.semantic.models import SemanticConcept, SemanticExtractionResult


DEFAULT_ONTOLOGY: dict[str, list[str]] = {
    "Authentication": ["authentication", "authenticate", "login", "jwt", "token", "password"],
    "Authorization": ["authorization", "authorize", "permission", "role", "access control"],
    "Session Management": ["session", "cookie", "refresh token"],
    "Payment": ["payment", "charge", "checkout", "card"],
    "Refund": ["refund", "reversal"],
    "Invoice": ["invoice", "billing"],
    "Customer": ["customer", "user", "account"],
    "Loan": ["loan", "lending", "emi"],
    "Notification": ["notification", "email", "sms", "slack"],
    "REST API": ["rest", "api", "endpoint", "http"],
}


class KeywordSemanticExtractor:
    """Deterministic semantic extractor with evidence-weighted confidence.

    Uses IDF-like keyword weights: a keyword appearing in only one concept
    category is a strong signal (weight=1.0); a keyword appearing in many
    categories is ambiguous (weight=0.2). Confidence floor is 0.30, ceiling
    is 0.95. Short content (< 50 tokens) gets a 0.80 multiplier.
    """

    def __init__(self, ontology: dict[str, list[str]] | None = None) -> None:
        self.ontology = ontology or DEFAULT_ONTOLOGY
        self._keyword_weights = self._compute_weights(self.ontology)

    @staticmethod
    def _compute_weights(ontology: dict[str, list[str]]) -> dict[str, float]:
        category_counts: dict[str, int] = {}
        for keywords in ontology.values():
            for kw in keywords:
                category_counts[kw] = category_counts.get(kw, 0) + 1
        return {kw: 1.0 / max(count, 1) for kw, count in category_counts.items()}

    async def extract(self, uko: UniversalKnowledgeObject) -> SemanticExtractionResult:
        source_text = " ".join(
            [
                uko.name,
                uko.content,
                " ".join(uko.metadata.tags),
            ]
        )
        haystack = self._normalize_text(source_text)
        token_count = len(haystack.split())

        concepts: list[SemanticConcept] = []
        for concept, keywords in self.ontology.items():
            evidence = [keyword for keyword in keywords if self._contains_term(haystack, keyword)]
            if not evidence:
                continue
            weighted_evidence = sum(self._keyword_weights.get(e, 0.1) for e in evidence)
            confidence = min(0.95, 0.55 + (0.12 * weighted_evidence))
            if token_count < 15:
                confidence *= 0.90
            concepts.append(
                SemanticConcept(
                    name=concept,
                    confidence=round(confidence, 4),
                    evidence=evidence,
                )
            )

        return SemanticExtractionResult(concepts=concepts)

    def _contains_term(self, haystack: str, term: str) -> bool:
        if " " in term:
            return term in haystack
        return re.search(rf"\b{re.escape(term)}\b", haystack) is not None

    def _normalize_text(self, value: str) -> str:
        spaced = re.sub(r"[_\-.\\/]+", " ", value)
        spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", spaced)
        return f"{value} {spaced}".lower()
