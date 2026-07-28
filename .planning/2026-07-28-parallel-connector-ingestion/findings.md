# Findings: Partitioned Parallel Connector Ingestion

## Current-system evidence

- The existing asynchronous worker safely isolates ingestion from the HTTP request.
- OpenClaw submission returned in 52 ms and early API health p95 was 18 ms.
- Extraction and structural derivation are CPU-heavy and can process tens of
  thousands of files.
- FalkorDB is a shared contention point; unrestricted graph work can degrade API and
  Docker responsiveness on a small local VM.
- A bounded single-worker run remained responsive with small chunks and extraction
  ceilings, confirming that resource isolation works but increases wall time.
- Scaling identical current workers would accelerate different repository jobs, not
  one repository, because one Redis delivery and one PostgreSQL lease own the job.

## Design consequence

The work must be split before extraction and joined before publication. Parallel
workers need disjoint immutable partitions. Their outputs need durable staging so
FalkorDB concurrency can be controlled separately.

## Initial operating hypothesis

- Four extraction workers are the first benchmark point.
- One graph writer remains the default.
- Partition weights must include file type/size/complexity.
- MinIO-backed Arrow/Parquet staging is preferred for large payloads, subject to a
  benchmark against PostgreSQL JSONB metadata.
- PostgreSQL remains authoritative for parent, partition, batch, lease and
  publication state.

