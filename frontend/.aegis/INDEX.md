# AegisAI Architecture Index

This is the Master Index for the AegisAI Architectural Specification. This `.aegis` directory serves as the immutable source of truth for the entire platform. Before a single line of code is written or modified, the architecture defined within these documents must be understood and respected.

---

## Folder Structure

The `.aegis` directory is organized into strict semantic categories:

```text
.aegis/
├── INDEX.md                 (This file)
├── core/                    (The foundational rules of the platform)
├── modules/                 (High-level component architectural designs)
├── specs/                   (Strict logical blueprints and APIs)
└── adrs/                    (Architectural Decision Records - Historical log)
```

---

## Read Order

For new engineers or AI assistants onboarding to the AegisAI codebase, the documents must be read in the following sequence to properly build mental context:

### Phase 1: The Foundation (Read First)
1.  `.aegis/core/architecture.md` (The grand vision and system layers)
2.  `.aegis/core/coding-rules.md` (How we write code)
3.  `.aegis/core/constitution.md` (The unviolable philosophy)

### Phase 2: The Specifications (The Blueprints)
4.  `.aegis/specs/technology-stack.md` (What tools we use)
5.  `.aegis/specs/database-schema.md` (The data foundation)
6.  `.aegis/specs/monorepo-bootstrap.md` (The physical repository layout)
7.  `.aegis/specs/docker-architecture.md` (How it runs in production)

### Phase 3: The Engine (The Core Mechanics)
8.  `.aegis/modules/governance-engine.md` (The absolute law)
9.  `.aegis/modules/runtime.md` (The execution loop)
10. `.aegis/modules/guardian.md` (The deep packet inspector)

### Phase 4: The Modules (Explore as needed)
*Read the remaining files in `.aegis/modules/` based on the specific feature being developed (e.g., `agent-lifecycle.md`, `hierarchy.md`, `builder.md`).*

---

## Document Status

All documents in `.aegis/core/` and `.aegis/specs/` are **LOCKED**. They represent the approved baseline.

All documents in `.aegis/modules/` are **LOCKED** unless an active ADR is open to modify a specific module.

*   **Locked Documents:** Cannot be modified without a formal ADR. Code must conform to these documents.
*   **Draft Documents:** In-progress designs. Code cannot be written based on draft documents.

---

## Dependency Graph

The architecture flows strictly downwards. A layer cannot bypass the layer below it.

1.  **Presentation:** `frontend-pages.md`, `builder.md`
    *   *depends on:*
2.  **Transport:** `api-contracts.md`, `agent-communication.md`
    *   *depends on:*
3.  **Governance:** `governance-engine.md`, `guardian.md`, `compliance.md`
    *   *depends on:*
4.  **Orchestration:** `runtime.md`, `tool-execution.md`, `provider-routing.md`
    *   *depends on:*
5.  **State:** `database-schema.md`, `storage.md`, `model-context.md`
    *   *depends on:*
6.  **Infrastructure:** `technology-stack.md`, `docker-architecture.md`

---

## Implementation Order

Implementation must follow `.aegis/specs/implementation-roadmap.md` strictly. Do not build Phase 3 features before Phase 1 is complete.

1.  Phase 1: The Foundation (Governance & Identity)
2.  Phase 2: The Guardian (Security & Policy)
3.  Phase 3: The Brain (Runtime & Context)
4.  Phase 4: The Memory (Knowledge & RAG)
5.  Phase 5: The Hands (Tools & Skills)
6.  Phase 6: The Glass (UI & Dashboards)
7.  Phase 7: Scale & Certify

---

## Rules for Updating Documentation

1.  **Code Follows Docs:** The `.aegis` directory is the master. If the code deviates from the documentation, the code is a bug.
2.  **The ADR Process:** If a fundamental shift in architecture is required (e.g., swapping Postgres for MongoDB, or removing the Guardian layer), an Architectural Decision Record (ADR) must be written, debated, and approved.
3.  **Update Propagation:** If an ADR is approved, all affected documents in `.aegis/` must be manually updated to reflect the new truth.
4.  **No Ghost Features:** If a feature does not exist in `.aegis/`, it cannot exist in `src/`.

---

## Rules for AI Assistants

If you are an AI coding assistant (like Antigravity or GitHub Copilot) operating within this repository, you are bound by the following directives:

1.  **Read Before Writing:** You must read the relevant `.aegis` specification before generating implementation code.
2.  **Enforce Governance:** You must never generate code that bypasses the Guardian module or raw-queries the database from the Presentation layer.
3.  **Halt on Conflict:** If a user requests a feature that explicitly violates `.aegis/core/constitution.md` or `.aegis/modules/governance-engine.md`, you must refuse the request and cite the architectural conflict.
4.  **No Hallucinated Architecture:** You must not invent new frameworks, libraries, or architectural patterns. Stick strictly to what is defined in `.aegis/specs/technology-stack.md`.

---

## Documentation Constitution

The permanent Documentation principles of AegisAI:
1. **The Principle of the Blueprint:** The building does not dictate the blueprint; the blueprint dictates the building. Documentation is not an afterthought written after the code; it is the contract written before it.
2. **The Principle of Absolute Truth:** There is only one source of truth for the system's design. If it is not in the `.aegis` folder, it is an unauthorized hallucination.
3. **The Principle of Institutional Memory:** We write it down so we do not have to remember it. We use ADRs so we understand not just *what* we built, but *why* we built it.
