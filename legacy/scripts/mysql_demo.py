import asyncio
from datetime import datetime, UTC
from ecms.core.uko import UKOMetadata, UKOType, UniversalKnowledgeObject
from ecms.pipeline.orchestrator import PipelineOrchestrator

ddl = """
CREATE TABLE customers (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255)
);
CREATE TABLE orders (
    id INT PRIMARY KEY,
    customer_id INT,
    amount DECIMAL(10,2),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
"""

uko = UniversalKnowledgeObject(
    id="mysql:table:test_db",
    type=UKOType.TABLE,
    name="test_db schema",
    content=ddl,
    metadata=UKOMetadata(
        source="mysql",
        source_id="test_db",
        created_at=datetime(2026,7,8, tzinfo=UTC),
        modified_at=datetime(2026,7,8, tzinfo=UTC),
    ),
)

orchestrator = PipelineOrchestrator()
episodes, write_result = asyncio.run(orchestrator.process_uko(uko))
ukos = [ep.uko for ep in episodes]
print(f"Total UKOs: {len(ukos)}")
print(f"Write: {write_result.success_count} success, {write_result.failure_count} failures")
for u in ukos:
    rels = " | ".join(f"{r.relationship}->{r.target_type.value}" for r in u.relationships)
    method = u.provenance.extraction_method if u.provenance else "none"
    print(f"  [{u.type.value:8s}] {u.name:35s} provenance={method:15s} edges=[{rels}]")
