# AegisAI Architecture Documentation Guide

Welcome to the `.aegis` directory. This directory is the immutable source of truth for the AegisAI platform. It contains the philosophy, architecture, and logical specifications that govern all code within this repository. 

**Code follows documentation. Documentation never follows code.**

---

## Purpose of `.aegis`
The purpose of this directory is to enforce a documentation-first engineering culture. By formally separating the *design* of the system from its *implementation*, we ensure that architectural constraints (specifically around Control, Governance, and Accountability) are mathematically upheld before a single line of code is written.

## Folder Responsibilities
*   **`.aegis/core/`**: The unchangeable foundation. Contains the platform's Constitution, core architectural diagrams, and strict coding rules.
*   **`.aegis/modules/`**: High-level designs for specific platform features (e.g., Governance Engine, Prompt Builder, Runtime).
*   **`.aegis/specs/`**: Explicit logical blueprints. Defines the database schemas, API contracts, UI pages, and technology stack.
*   **`.aegis/adrs/`**: Architectural Decision Records. A historical log of significant changes to the platform's design.

## Documentation Philosophy
1.  **Immutability by Default:** Documents are considered locked once approved. They are not living wikis to be casually edited.
2.  **Absolute Truth:** If the code behaves differently than the `.aegis` documentation, the code contains a bug.
3.  **Explain "Why", not just "What":** Good documentation explains the rationale behind a decision to prevent future engineers from repeating past mistakes.

## Read Order
If you are new to the AegisAI project, you **must** read the documentation in the following order to understand the platform:
1.  `core/constitution.md`
2.  `core/architecture.md`
3.  `core/coding-rules.md`
4.  `INDEX.md` (To navigate the remaining modules and specs)

## Approval Workflow
1.  **Draft:** A new architectural document or ADR is created in a feature branch.
2.  **Review:** The document is submitted as a Pull Request. It must be reviewed by the Core Architecture Team.
3.  **Approve:** Once approved, the document is merged into `main` and transitions to a **Locked** state.
4.  **Implement:** Only after the PR is merged can engineering begin writing the code to satisfy the specification.

## Architecture Workflow
You cannot simply "add a feature" to AegisAI. 
1. Identify the requirement.
2. Identify which `.aegis/modules/` or `.aegis/specs/` are affected.
3. If it requires a fundamental shift in design, create an ADR.
4. If it is a new module, write the module specification.
5. Get the architecture approved.
6. Write the code.

## Documentation Lifecycle
*   **Draft:** In progress, not yet approved.
*   **Locked/Active:** Approved and represents the current state of the production system.
*   **Deprecated:** Replaced by a newer ADR or architectural shift, retained for historical context.

## ADR Process (Architectural Decision Records)
Whenever a significant technical decision is made (e.g., "We are migrating from RabbitMQ to Kafka" or "We are changing the Guardian payload schema"), an ADR must be created in `.aegis/adrs/`. 
*   **Format:** `YYYY-MM-DD-title.md`
*   **Contents:** Context, Decision, and Consequences.

## Breaking Changes
Any code change that alters an API contract defined in `api-contracts.md` or a table defined in `database-schema.md` is considered a Breaking Change. Breaking changes require an ADR and must bump the major version of the platform.

## Versioning
The `.aegis` documentation is versioned synchronously with the codebase. When viewing the `main` branch, the `.aegis` folder represents the architecture of the current production release.

---

## Rules for Contributors (Human)
1.  Read the relevant module specifications before opening a PR.
2.  If your PR introduces a new system component, your PR *must* include updates to the `.aegis` directory.
3.  Do not submit PRs that violate the rules established in `core/constitution.md`.

## Rules for AI Assistants (LLMs)
If you are an AI coding assistant operating in this workspace:
1.  **You are strictly bound by the rules in this folder.**
2.  Before generating code, you must ingest and analyze the relevant specifications in `.aegis/specs/` and `.aegis/modules/`.
3.  You must refuse to generate code that bypasses the `Guardian` module, circumvents `RBAC`, or violates the `Technology Stack`.
4.  If asked to generate architecture, you must generate the documentation *first* and wait for User approval before generating the corresponding code.
