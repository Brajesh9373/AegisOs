# AegisAI Modules Architecture Index

Welcome to the `.aegis/modules/` directory. This folder contains the high-level architectural designs for every major component (module) of the AegisAI platform. A "module" is a logical grouping of functionality that can span across the API, Database, and UI layers.

This README serves as the map to these modules.

---

## Module Groupings by Domain

### Domain: Foundation & Identity
Modules responsible for establishing the tenant boundary and Human identity.
*   `identity.md` - Authentication, Sessions, SAML/SSO.
*   `platform-bootstrap.md` - The genesis setup sequence.
*   `hierarchy.md` - The structural DAG of Orgs, Departments, Teams, and Agents.

### Domain: Governance & Control
The core enforcement mechanisms. These modules sit above everything else.
*   `governance-engine.md` - The central decision matrix (ALLOW/DENY/SUSPEND).
*   `guardian.md` - The Deep Packet Inspection payload scanner.
*   `compliance.md` - Data residency, GDPR, and regional rule enforcement.

### Domain: Execution & Runtime
The brain of the AI workforce.
*   `runtime.md` - The core execution loop (Thought, Action, Observation).
*   `tool-execution.md` - Sandboxed execution of external kinetic actions.
*   `provider-routing.md` - Abstraction layer for LLM APIs (OpenAI, Anthropic, Local).
*   `agent-communication.md` - Secure, governed message passing between Agents.

### Domain: Context & Memory
How Agents perceive the world and remember the past.
*   `model-context.md` - The strict boundary of what an Agent is allowed to "know."
*   `context-builder.md` - The pipeline that fetches RBAC-filtered data for the prompt.
*   `prompt-builder.md` - The system that aggregates System, Org, and Task instructions.

### Domain: Presentation & UX
How Humans configure and interact with the AI workforce.
*   `builder.md` - The visual, no-code configuration wizards.
*   `agent-lifecycle.md` - The state machine governing an Agent from Draft to Retirement.

### Domain: Data & Infrastructure
The persistent persistence layers.
*   `storage.md` - Object storage (S3/MinIO) for attachments and RAG chunks.
*   `search.md` - Vector Database (pgvector) and Full-Text Search (Elasticsearch).

### Domain: Operations & Audit
How the system is monitored and how humans are held accountable.
*   `observability.md` - Traces, metrics, logs, and RCA workflows.
*   `performance.md` - SLA targets, caching, and horizontal scaling limits.

---

## Dependency Order

A module cannot be implemented if it depends on a module that does not exist. The architectural dependency flows as follows:

1.  **Identity & Hierarchy** (Without Humans and boundaries, nothing exists).
    *   *depends on -> Database/Storage.*
2.  **Governance & Guardian** (The rule of law).
    *   *depends on -> Identity & Hierarchy.*
3.  **Context & Prompting** (Forming the thoughts).
    *   *depends on -> Governance (to filter forbidden data).*
4.  **Runtime & Execution** (The kinetic action).
    *   *depends on -> Context & Prompting (to know what to do).*
    *   *depends on -> Governance (to ask permission before doing it).*
5.  **Presentation (Builders & UX)** (The Human interface).
    *   *depends on -> All of the above (via REST APIs).*

---

## Implementation Order

Implementation must follow the Phased roadmap defined in `.aegis/specs/implementation-roadmap.md`. Do not attempt to build a Phase 5 module before Phase 2 is complete.

*   **Phase 1:** `identity.md`, `platform-bootstrap.md`, `hierarchy.md`
*   **Phase 2:** `governance-engine.md`, `guardian.md`, `compliance.md`
*   **Phase 3:** `runtime.md`, `provider-routing.md`, `context-builder.md`, `prompt-builder.md`
*   **Phase 4:** `model-context.md`, `search.md`, `storage.md`
*   **Phase 5:** `tool-execution.md`, `agent-communication.md`
*   **Phase 6:** `builder.md`, `agent-lifecycle.md`
*   **Phase 7:** `performance.md`, `observability.md`

---

## Ownership

Modules are owned by the Architecture Team. Individual engineers cannot unilaterally modify a module document. 

Implementation of these modules spans the monorepo:
*   The **Backend AI Persona** owns the implementation of Runtime, Governance, and Data domains in `apps/api` and internal `packages/`.
*   The **Frontend AI Persona** owns the implementation of the Presentation domain in `apps/web`.

---

## Governance Integration

The following modules represent the Governance enforcement layer. Every other module MUST yield to them.
*   `governance-engine.md`
*   `guardian.md`

If `tool-execution.md` outlines how to call the Jira API, it must explicitly state that it waits for a `governance-engine` ALLOW decision before doing so. 

## Runtime Integration

The following modules represent the active thought loop.
*   `runtime.md`
*   `provider-routing.md`
*   `tool-execution.md`

The Runtime is the only module permitted to directly interface with an external LLM Provider. No other module (e.g., the Web Frontend or the Search module) is allowed to bypass the Runtime to talk to OpenAI. 

## Guardian Integration

`guardian.md` is the Deep Packet Inspector.
*   The `runtime.md` sends outbound LLM Prompts to Guardian before transmission.
*   The `runtime.md` sends inbound LLM Responses to Guardian before parsing.
*   The `agent-communication.md` sends message payloads to Guardian before queuing.
*   The `builder.md` sends configuration drafts to Guardian before publishing.
