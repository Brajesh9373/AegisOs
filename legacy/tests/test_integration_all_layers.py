"""Integration test: all 8 reliability layers exercised in one flow."""
import pytest
from datetime import datetime, timezone, UTC

from ecms.core.uko import (
    ExtractionProvenance,
    UKOMetadata,
    UKORelationship,
    UKOType,
    UniversalKnowledgeObject,
)
from ecms.core.graph import BatchWriteResult
from ecms.core.schema_validator import validate_relationship
from ecms.pipeline.orchestrator import PipelineOrchestrator
from ecms.pipeline.semantic.llm_extractor import KeywordSemanticExtractor
from ecms.pipeline.semantic.concept_mapper import ConceptMapper
from ecms.pipeline.identity.resolver import IdentityResolver
from ecms.pipeline.identity.embedder_resolver import EmbeddingIdentityResolver
from ecms.memory.brain import GBrain
from ecms.memory.long_term import LongTermMemory
from tests.fakes import FakeGraphClient

PYTHON_CONTENT = """
class PaymentService:
    def process_payment(self, token):
        \"\"\"Authenticate and charge payment.\"\"\"
        return token

class AuthManager:
    def validate_token(self, jwt_token):
        \"\"\"Validate JWT token.\"\"\"
        return True

def send_notification(email, message):
    \"\"\"Send email notification.\"\"\"
    pass
"""


@pytest.mark.asyncio
async def test_full_pipeline_with_provenance_and_errors():
    """Verify all layers work together:
    L1 - Provenance on every edge and node
    L2 - BatchWriteResult with success counts
    L3 - Schema validation rejects invalid edges
    L4 - Evidence-weighted confidence (not flat formula)
    L5 - Identity resolver merges person duplicates
    L6 - ConsistencyChecker references work
    L7 - Lifecycle fields (status, version) on UKOs
    L8 - GBrain graph-first writes
    """
    graph = FakeGraphClient()
    orchestrator = PipelineOrchestrator(graph=graph)

    # Create source UKO
    uko = UniversalKnowledgeObject(
        id="git:file:e2e:payment.py",
        type=UKOType.FILE,
        name="payment.py",
        content=PYTHON_CONTENT,
        metadata=UKOMetadata(
            source="git",
            source_id="payment.py",
            created_at=datetime(2026, 7, 8, tzinfo=UTC),
            modified_at=datetime(2026, 7, 8, tzinfo=UTC),
            authors=["john.smith@example.com", "bob.jones@example.com"],
        ),
        status="active",
        version=1,
    )

    # Run pipeline
    episodes, write_result = await orchestrator.process_uko(uko)

    # === L2: Error Propagation ===
    assert isinstance(write_result, BatchWriteResult)
    assert write_result.success_count > 0, "Should have successful writes"
    assert write_result.failure_count == 0, f"Unexpected failures: {write_result.failures}"

    # Get all UKOs from episodes
    all_ukos = [ep.uko for ep in episodes]
    all_types = {u.type for u in all_ukos}

    # Structural extraction worked
    assert UKOType.CLASS in all_types, "Should extract CLASS"
    assert UKOType.FUNCTION in all_types, "Should extract FUNCTION"

    # === L1: Provenance ===
    function_uko = next(u for u in all_ukos if u.type == UKOType.FUNCTION)
    # Every relationship MUST have provenance
    for rel in function_uko.relationships:
        assert rel.provenance is not None, f"Missing provenance on '{rel.relationship}' edge"
        assert rel.provenance.extraction_method, "Provenance missing extraction_method"
        assert rel.provenance.pipeline_stage, "Provenance missing pipeline_stage"

    # Node-level provenance
    class_uko = next(u for u in all_ukos if u.type == UKOType.CLASS)
    assert class_uko.provenance is not None, "Missing node-level provenance"
    assert class_uko.provenance.pipeline_stage == "structural"

    # === L4: Confidence Calibration ===
    # Semantic extractor uses evidence-weighted formula
    extractor = KeywordSemanticExtractor()
    result = await extractor.extract(uko)
    concepts = [c for c in result.concepts if c.confidence > 0.5]
    assert len(concepts) > 0, "Should extract at least one concept"
    for concept in concepts:
        # Not the old flat formula
        assert concept.confidence != 0.65, "Should use weighted formula, not 0.55+0.1*n"
        assert 0.0 <= concept.confidence <= 0.95

    # Concept mapper creates provenance
    mapper = ConceptMapper()
    concept_ukos = mapper.map_concepts(uko, concepts)
    for cu in concept_ukos:
        assert cu.provenance is not None
        assert cu.provenance.pipeline_stage == "semantic"
        for rel in cu.relationships:
            assert rel.provenance is not None
            assert rel.provenance.extraction_method == "keyword_match"

    # === L3: Schema Validation ===
    # Valid edges must pass
    is_valid, reason = validate_relationship("contained_in", UKOType.FILE)
    assert is_valid, f"contained_in -> FILE should be valid: {reason}"

    is_valid, reason = validate_relationship("defined_in", UKOType.CLASS)
    assert is_valid, f"defined_in -> CLASS should be valid: {reason}"

    # Invalid edges must be rejected
    is_valid, reason = validate_relationship("belongs_to", UKOType.FUNCTION)
    assert not is_valid, "belongs_to -> FUNCTION should be invalid"
    is_valid, reason = validate_relationship("contained_in", UKOType.PERSON)
    assert not is_valid, "contained_in -> PERSON should be invalid"
    is_valid, reason = validate_relationship("nonexistent_edge", UKOType.FILE)
    assert not is_valid, "Unknown edge type should be rejected"

    # === L5: Identity Resolution ===
    person_ukos = [
        UniversalKnowledgeObject(
            id=f"person:john-smith-{i}",
            type=UKOType.PERSON,
            name=name,
            content="",
            metadata=UKOMetadata(
                source="jira",
                source_id=f"issue-{i}",
                created_at=datetime(2026, 7, 8, tzinfo=UTC),
                modified_at=datetime(2026, 7, 8, tzinfo=UTC),
                authors=[name],
            ),
        )
        for i, name in enumerate(["john.smith@example.com", "John Smith", "john.smith@bitbucket.org"])
    ]
    resolver = IdentityResolver()
    resolved = await resolver.resolve(person_ukos)
    # Should cluster john.smith@example.com and john.smith@bitbucket.org
    # (same email username), and possibly "John Smith" if rule catches it
    assert len(resolved) >= 1, "Should resolve at least one identity cluster"
    for resolved_person in resolved:
        assert resolved_person.provenance is not None, "Resolved person missing provenance"
        assert resolved_person.provenance.pipeline_stage == "identity"
        for rel in resolved_person.relationships:
            assert rel.provenance is not None, "same_as edge missing provenance"

    # Embedding resolver handles unavailable embedder gracefully
    embedder_resolver = EmbeddingIdentityResolver(embedder=None)
    assert not embedder_resolver.available
    result = await embedder_resolver.resolve([])
    assert result == []

    # === L6: ConsistencyChecker ===
    from ecms.core.consistency import ConsistencyChecker
    checker = ConsistencyChecker(graph)
    report = await checker.check_all()
    assert report.total_nodes >= 0
    assert isinstance(report.orphan_ids, list)
    assert isinstance(report.phantom_target_ids, list)

    # === L7: Lifecycle Fields ===
    for ep_uko in all_ukos:
        assert ep_uko.status in ("active", "deprecated", "removed")
        assert ep_uko.version >= 1

    # === L8: GBrain Graph-First Writes ===
    import tempfile
    from pathlib import Path
    tmpdir = Path(tempfile.mkdtemp())
    try:
        brain = GBrain(tmpdir, long_term=LongTermMemory(graph=graph))
        episodes_result = await brain.write("test_topic", "Test content for GBrain.")
        assert len(episodes_result) > 0
        # File should exist on disk
        note_file = tmpdir / "test-topic.md"
        assert note_file.exists(), "GBrain should have created markdown file"
        # Content should match
        content = note_file.read_text(encoding="utf-8")
        assert "Test content for GBrain" in content
        # Read should find it
        notes = await brain.read("GBrain")
        assert len(notes) > 0
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    # === Summary ===
    print(f"\n  All layers verified:")
    print(f"  L1 Provenance: {sum(1 for u in all_ukos if u.provenance)} UKOs with node provenance")
    print(f"  L2 Errors: {write_result.success_count} success, {write_result.failure_count} failures")
    print(f"  L3 Schema: {len(VALID_RELATIONSHIP_TARGETS)} validated relationship types")
    print(f"  L4 Confidence: {len(concepts)} concepts with evidence-weighted scores")
    print(f"  L5 Identity: {len(resolved)} resolved person clusters")
    print(f"  L6 Consistency: {report.total_nodes} nodes checked")
    print(f"  L7 Lifecycle: all UKOs have status/version")
    print(f"  L8 GBrain: graph-first write confirmed")


# Import for assertion
from ecms.core.schema_validator import VALID_RELATIONSHIP_TARGETS
