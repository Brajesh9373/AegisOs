# Skill Standard Specification

## Purpose

The **Skill Standard** establishes the universal, immutable specification for every single AI Agent Skill within the AegisAI platform. Because Skills act as the atomic units of execution modifying the environment, they must be rigorously defined, safely bounded, and completely predictable. No Skill may be introduced to the platform without strictly satisfying this entire structural specification.

---

## 1. The Skill Definition Contract

Every Skill definition must structurally encapsulate the following properties:

### 1.1 Identity & Ownership

- **Identity:** A globally unique, semantic identifier (e.g., `aegis.core.fs.write_file`).
- **Version:** Semantic versioning (e.g., `v1.2.0`) to ensure backwards compatibility within workflows.
- **Owner:** The explicit Engineering Team or Digital Team responsible for the Skill's maintenance and security.
- **Description:** A concise, business-readable explanation of what the Skill accomplishes.

### 1.2 I/O & Boundaries

- **Inputs:** Strongly-typed Zod schemas defining exactly what arguments the Skill accepts.
- **Outputs:** Strongly-typed payloads detailing the explicit data returned upon success.
- **Preconditions:** The exact environmental states or previous node outputs that must be true _before_ execution begins.
- **Postconditions:** The guaranteed environmental state _after_ successful execution.

### 1.3 Execution Requirements

- **Required Permissions:** Explicit granular Guardian scopes requested (e.g., `fs:write:/app/src`).
- **Required Tools:** The underlying low-level APIs or CLI binaries utilized by the Skill.
- **Required Knowledge:** Specific RAG domains or context vectors necessary for the Skill to reason effectively.

### 1.4 Resiliency & Governance

- **Execution Timeout:** The strict maximum duration (TTL in milliseconds) before the Runtime forcefully aborts the Skill.
- **Retry Policy:** Maximum retry limit and backoff multiplier for transient failures.
- **Rollback Strategy:** An explicit inverse operation that can be executed to reverse the Skill's mutation if subsequent validation fails.
- **Validation Rules:** The automated logic used to prove the Skill achieved its Postconditions.

### 1.5 Observability & Audit

- **Evidence Produced:** The exact artifacts generated for human verification (e.g., unified diffs, HTTP response codes, screenshots).
- **Errors:** Explicitly enumerated fatal failure states (no generic exceptions).
- **Warnings:** Explicit non-fatal friction points.
- **Metrics:** Custom telemetry data points emitted to DWI (e.g., tokens consumed, latency).
- **Audit Data:** The specific fields serialized into the WORM (Write-Once-Read-Many) compliance ledger.

### 1.6 Architectural Constraints

- **Dependencies:** Other Skills or internal Packages this Skill relies on.
- **Security Requirements:** Zero-trust mandates (e.g., masking credentials in logs, API key handling).
- **Compliance Requirements:** Regulatory boundaries (e.g., GDPR data stripping, localized execution regions).

### 1.7 Usability

- **Examples:** Complete payload examples demonstrating valid Inputs mapped to valid Outputs.

---

## 2. The Skill Lifecycle

Skills are not static; they evolve. To protect active Implementation Projects from breaking changes, every Skill undergoes a strict lifecycle tracked by the Registry.

1. **Draft:** The Skill is currently under development. It can only be executed in isolated `/scratch/` or local test environments.
2. **Testing:** The Skill is structurally complete and actively undergoing integration tests against the Guardian and Runtime engines.
3. **Approved:** The Skill has passed Architectural Review and is available in the Marketplace for production assignment to Digital Employees.
4. **Deprecated:** The Skill is scheduled for removal. Active workflows may continue to use it, but the Builder UI will warn users and prevent new assignments.
5. **Archived:** The Skill is permanently deactivated. It remains in the registry strictly for historical audit replay, but execution is architecturally blocked by the Runtime.

---

## Implementation Mapping

- **Owner Package:** [To Be Defined]
- **Owner Modules:** [To Be Defined]
- **Related Packages:** [To Be Defined]
- **Required Contracts:** [To Be Defined]
- **Required Types:** [To Be Defined]
- **Required Runtime Components:** [To Be Defined]
- **Required Builder Components:** [To Be Defined]
- **Required APIs:** [To Be Defined]
- **Required Database Models:** [To Be Defined]
- **Required Workflows:** [To Be Defined]
- **Required Skills:** [To Be Defined]
- **Required Tests:** [To Be Defined]
- **Verification Commands:** [To Be Defined]
- **Roadmap Phase:** [To Be Defined]
- **Implementation Status:** [Not Started | In Progress | Completed | Frozen]
