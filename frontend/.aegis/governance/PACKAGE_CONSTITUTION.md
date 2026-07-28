# Package Constitution

## Purpose

While the Repository Constitution defines the overarching engineering processes for AegisAI, the **Package Constitution** serves as the definitive structural governance document. It explicitly maps every monorepo package to its architectural responsibility, dictates strict dependency hierarchies, and outlines the immutable laws preventing cross-package contamination.

This document ensures the AegisAI platform scales infinitely without succumbing to the monolithic entanglement of "big ball of mud" architecture.

---

## Dependency Rules

To prevent architectural contamination, the platform enforces a strict, unidirectional topological dependency graph.

**Core Dependency Graph:**
`types` ↓ `contracts` ↓ `shared` ↓ `config` ↓ `runtime`

- **No circular dependencies:** Circular imports are treated as fatal build errors (enforced via Madge).
- **No architectural bypassing:** Packages may not reach across isolated bounded contexts (e.g., `ui` cannot directly depend on `database`; it must consume the `sdk`).
- **No upward dependencies:** Lower-level packages (e.g., `types`, `contracts`) can never depend on higher-level packages (e.g., `runtime`, `workflow`).

---

## Package Definitions

### `@aegisai/types`

- **Purpose:** Pure structural definitions devoid of business logic.
- **Primary Responsibility:** Exposing foundational platform TypeScript interfaces and branded types.
- **Package Owner:** Core Platform Team
- **Public API Responsibility:** Defining absolute baseline data shapes.
- **Internal Responsibilities:** Enforcing type safety platform-wide.
- **Allowed Dependencies:** None (Absolute bottom of the dependency graph).
- **Forbidden Dependencies:** All internal packages.
- **External Dependencies:** Zero-dependency (beyond TS).
- **Future Expansion Rules:** Types should only be added if they are universally applicable across multiple packages.
- **Classification:** Core Platform
- **Implementation Status:** Stable

### `@aegisai/contracts`

- **Purpose:** Protocol and interface definitions.
- **Primary Responsibility:** Defining bounded context interactions, message payloads, and abstract interfaces.
- **Package Owner:** Core Platform Team
- **Public API Responsibility:** Contractually binding APIs that external systems must satisfy.
- **Internal Responsibilities:** Allowing dependency inversion across the platform.
- **Allowed Dependencies:** `@aegisai/types`
- **Forbidden Dependencies:** Implementations (`runtime`, `database`, `provider`).
- **External Dependencies:** `zod` (for schema validation).
- **Future Expansion Rules:** Contracts must never leak underlying implementation details (e.g., no SQL-specific types).
- **Classification:** Core Platform
- **Implementation Status:** Stable

### `@aegisai/shared`

- **Purpose:** Common functional utilities.
- **Primary Responsibility:** Providing stateless helpers, array manipulations, UUID generation, and custom error classes.
- **Package Owner:** Core Platform Team
- **Public API Responsibility:** Exposing predictable, pure functions.
- **Internal Responsibilities:** Preventing duplicated utility logic across packages.
- **Allowed Dependencies:** `@aegisai/types`, `@aegisai/contracts`
- **Forbidden Dependencies:** `config`, `runtime`, and any stateful packages.
- **External Dependencies:** Approved utility libraries (e.g., `lodash-es` if necessary).
- **Future Expansion Rules:** Only completely stateless, pure functions are permitted.
- **Classification:** Infrastructure
- **Implementation Status:** Stable

### `@aegisai/config`

- **Purpose:** Centralized platform configuration.
- **Primary Responsibility:** Parsing, validating, and injecting environment variables and platform policies.
- **Package Owner:** DevOps / Platform Eng
- **Public API Responsibility:** Abstracting environment complexity.
- **Internal Responsibilities:** Providing typed configurations to the runtime.
- **Allowed Dependencies:** `@aegisai/types`, `@aegisai/contracts`, `@aegisai/shared`
- **Forbidden Dependencies:** `runtime`, `database`.
- **External Dependencies:** `dotenv`
- **Future Expansion Rules:** Must never store raw secrets in source; relies strictly on external environment injection.
- **Classification:** Infrastructure
- **Implementation Status:** Stable

### `@aegisai/runtime`

- **Purpose:** The core engine of the platform.
- **Primary Responsibility:** Bootstrapping the application, resolving dependencies, and managing lifecycle states.
- **Package Owner:** Core Platform Team
- **Public API Responsibility:** Providing the application host boundary.
- **Internal Responsibilities:** Orchestrating DI containers and gracefully shutting down services.
- **Allowed Dependencies:** `types`, `contracts`, `shared`, `config`
- **Forbidden Dependencies:** `ui`, `sdk`, `marketplace`.
- **External Dependencies:** IoC containers, Fastify (or equivalent HTTP server).
- **Future Expansion Rules:** The runtime remains ignorant of specific business workflows; it strictly runs code.
- **Classification:** Execution
- **Implementation Status:** Stable

### `@aegisai/database`

- **Purpose:** Persistent state storage.
- **Primary Responsibility:** Managing connections, migrations, and repository implementations.
- **Package Owner:** Core Platform Team
- **Public API Responsibility:** Abstracted data access layers (Repositories).
- **Internal Responsibilities:** Safeguarding schema integrity.
- **Allowed Dependencies:** `types`, `contracts`, `shared`, `config`
- **Forbidden Dependencies:** `runtime` (Runtime injects it, DB doesn't depend on Runtime).
- **External Dependencies:** ORMs (e.g., Prisma, Drizzle), PostgreSQL drivers.
- **Future Expansion Rules:** Must abstract query languages behind contract interfaces.
- **Classification:** Infrastructure
- **Implementation Status:** Planned

### `@aegisai/sdk`

- **Purpose:** Client consumption.
- **Primary Responsibility:** Providing a strongly-typed HTTP wrapper for external interaction with the platform.
- **Package Owner:** Developer Experience Team
- **Public API Responsibility:** Securely routing commands to the AegisAI API.
- **Internal Responsibilities:** Abstracting REST/GraphQL communication.
- **Allowed Dependencies:** `types`, `contracts`
- **Forbidden Dependencies:** `runtime`, `database`, `shared` (keep client bundle small).
- **External Dependencies:** HTTP clients (e.g., `fetch`, `axios`).
- **Future Expansion Rules:** Must remain isomorphic (run in Node and Browser).
- **Classification:** Developer Experience
- **Implementation Status:** Planned

### `@aegisai/ui`

- **Purpose:** Visual interface components.
- **Primary Responsibility:** Providing reusable React/Vue components for platform dashboards.
- **Package Owner:** Product Engineering
- **Public API Responsibility:** Rendering accessible, responsive UI.
- **Internal Responsibilities:** Maintaining design system consistency.
- **Allowed Dependencies:** `types`, `sdk`
- **Forbidden Dependencies:** `database`, `runtime`, `contracts` (directly).
- **External Dependencies:** React, TailwindCSS.
- **Future Expansion Rules:** Must remain purely presentational, relying on the SDK for state mutations.
- **Classification:** Business Layer
- **Implementation Status:** Planned

### `@aegisai/workflow`

- **Purpose:** DAG orchestration.
- **Primary Responsibility:** Coordinating multi-agent graphs, state transitions, and asynchronous tasks.
- **Package Owner:** Core Execution Team
- **Public API Responsibility:** Exposing workflow definitions and state triggers.
- **Internal Responsibilities:** Handling retry logic, branching, and blocking tasks.
- **Allowed Dependencies:** `types`, `contracts`, `shared`
- **Forbidden Dependencies:** `database` (directly).
- **External Dependencies:** Workflow engines.
- **Future Expansion Rules:** Must remain entirely decoupled from specific LLM models.
- **Classification:** Execution
- **Implementation Status:** Planned

### `@aegisai/guardian`

- **Purpose:** Security and authorization.
- **Primary Responsibility:** Ensuring zero-trust execution, checking permissions, and sandboxing AI commands.
- **Package Owner:** Security Engineering
- **Public API Responsibility:** Approval gate management.
- **Internal Responsibilities:** Halting execution on policy violations.
- **Allowed Dependencies:** `types`, `contracts`, `shared`, `config`
- **Forbidden Dependencies:** None conceptually, but sits as middleware above execution logic.
- **External Dependencies:** Crypto libraries.
- **Future Expansion Rules:** Fails closed by default; never bypassable.
- **Classification:** Security
- **Implementation Status:** Planned

### `@aegisai/provider`

- **Purpose:** External system abstraction.
- **Primary Responsibility:** Normalizing third-party APIs (LLMs, Identity Providers, SaaS tools).
- **Package Owner:** Platform Integrations
- **Public API Responsibility:** Standardized interfaces to diverse external systems.
- **Internal Responsibilities:** Handling rate limits, API keys, and connection pooling.
- **Allowed Dependencies:** `types`, `contracts`, `shared`
- **Forbidden Dependencies:** `database`, `runtime`.
- **External Dependencies:** External SDKs (OpenAI, AWS, Azure).
- **Future Expansion Rules:** Must adapt external schemas perfectly to internal Contracts.
- **Classification:** Infrastructure
- **Implementation Status:** Planned

### `@aegisai/knowledge`

- **Purpose:** Vector and semantic indexing.
- **Primary Responsibility:** RAG (Retrieval-Augmented Generation) pipeline, ingesting documents, and contextual retrieval.
- **Package Owner:** AI Engineering
- **Public API Responsibility:** Semantic search querying.
- **Internal Responsibilities:** Chunking, embedding, and ranking.
- **Allowed Dependencies:** `types`, `contracts`, `shared`
- **Forbidden Dependencies:** `memory`.
- **External Dependencies:** Vector databases, embedding models.
- **Future Expansion Rules:** Must support isolated tenant indexes.
- **Classification:** Execution
- **Implementation Status:** Planned

### `@aegisai/memory`

- **Purpose:** Episodic agent state tracking.
- **Primary Responsibility:** Recording short-term context and long-term execution history for agents.
- **Package Owner:** AI Engineering
- **Public API Responsibility:** Memory injection for agents.
- **Internal Responsibilities:** Pruning old memories, context window summarization.
- **Allowed Dependencies:** `types`, `contracts`, `shared`
- **Forbidden Dependencies:** `knowledge`.
- **External Dependencies:** None (relies on Contracts to save to Database).
- **Future Expansion Rules:** Strictly decoupled from factual `knowledge`.
- **Classification:** Execution
- **Implementation Status:** Planned

### `@aegisai/audit`

- **Purpose:** Immutable logging.
- **Primary Responsibility:** Recording cryptographic, tamper-evident logs of every structural platform change.
- **Package Owner:** Security Engineering
- **Public API Responsibility:** Writing to the Write-Once-Read-Many (WORM) ledger.
- **Internal Responsibilities:** Maintaining compliance trails.
- **Allowed Dependencies:** `types`, `contracts`, `shared`
- **Forbidden Dependencies:** None.
- **External Dependencies:** Crypto hashing utilities.
- **Future Expansion Rules:** Logs can never be deleted or updated; only appended.
- **Classification:** Security
- **Implementation Status:** Planned

### `@aegisai/monitoring`

- **Purpose:** Telemetry and observability.
- **Primary Responsibility:** Capturing metrics, traces, and system health status.
- **Package Owner:** DevOps
- **Public API Responsibility:** Exposing Prometheus/OpenTelemetry endpoints.
- **Internal Responsibilities:** Aggregating errors and latencies.
- **Allowed Dependencies:** `types`, `contracts`, `shared`
- **Forbidden Dependencies:** `database`.
- **External Dependencies:** OpenTelemetry, Prometheus SDKs.
- **Future Expansion Rules:** Telemetry must be completely non-blocking to the runtime.
- **Classification:** Infrastructure
- **Implementation Status:** Planned

### `@aegisai/builder`

- **Purpose:** Visual, no-code workflow creation.
- **Primary Responsibility:** Generating verifiable Implementation Graphs without writing code.
- **Package Owner:** Product Engineering
- **Public API Responsibility:** Exposing visual graph nodes.
- **Internal Responsibilities:** Serializing visual graphs into executable workflow payloads.
- **Allowed Dependencies:** `types`, `contracts`, `shared`, `ui`
- **Forbidden Dependencies:** `runtime`, `database`.
- **External Dependencies:** Diagramming libraries (e.g., React Flow).
- **Future Expansion Rules:** The builder generates state; the runtime executes it. They are separate.
- **Classification:** Developer Experience
- **Implementation Status:** Planned

### `@aegisai/marketplace`

- **Purpose:** Asset distribution.
- **Primary Responsibility:** Packaging, signing, and serving Implementation Templates and Knowledge Packs.
- **Package Owner:** Ecosystem Engineering
- **Public API Responsibility:** Serving the marketplace index and downloading assets.
- **Internal Responsibilities:** Cryptographically verifying packages.
- **Allowed Dependencies:** `types`, `contracts`, `shared`
- **Forbidden Dependencies:** `runtime`, `workflow` (it distributes, it does not execute).
- **External Dependencies:** Signing utilities.
- **Future Expansion Rules:** Follows the pure self-hosted distribution model defined in the Blueprint.
- **Classification:** Marketplace
- **Implementation Status:** Planned

---

## Package Laws

1. **One responsibility per package:** No package may manage two bounded contexts.
2. **No duplicate ownership:** Only one package is authoritative for a given domain entity.
3. **No circular dependencies:** Forbidden mathematically by the build pipeline.
4. **No hidden dependencies:** Every dependency must be explicitly declared in `package.json`.
5. **Public APIs must remain stable:** Minor changes require ADRs; major changes require RFCs.
6. **No architectural bypass:** Boundaries established in the Blueprint cannot be circumvented for convenience.

---

## Definition of Done

A package implementation task is officially complete _only_ if:

1. **Build passes:** Topological compilation succeeds cleanly.
2. **Typecheck passes:** Zero `tsc` errors.
3. **Lint passes:** Zero ESLint or Prettier warnings.
4. **Tests pass:** 100% of defined Vitest cases execute successfully.
5. **Documentation complete:** The package's `README.md` is updated and accurate.
6. **Public API documented:** Exported methods and interfaces are heavily commented.
7. **Architecture compliant:** The execution logic strictly aligns with the Constitutional Blueprint and these Governance laws.

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
