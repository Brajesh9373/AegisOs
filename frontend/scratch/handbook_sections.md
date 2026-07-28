## Platform Capability Map

### Identity
- **Purpose**: Authenticates system actors and manages sessions.
- **Responsibilities**: Token issuance, credential verification.
- **Owner**: Security Architecture Team.
- **Consumers**: Guardian, API, Runtime.
- **Dependencies**: IdP Providers.
- **Future evolution**: Decentralized Identity (DID) integration.

### Workspace
- **Purpose**: Provides logical isolation boundaries for resources.
- **Responsibilities**: Grouping agents, knowledge, and execution environments.
- **Owner**: Core Engineering Team.
- **Consumers**: Agents, Knowledge Engine.
- **Dependencies**: Database, Organization.
- **Future evolution**: Cross-workspace secure resource sharing.

### Organization
- **Purpose**: High-level tenant management.
- **Responsibilities**: Billing aggregation, global policy application.
- **Owner**: Platform Architecture Team.
- **Consumers**: Licensing, Billing.
- **Dependencies**: Database.
- **Future evolution**: Hierarchical tenant structures.

### Runtime
- **Purpose**: The core execution loop.
- **Responsibilities**: Application boot, state management, dependency injection.
- **Owner**: Core Engineering Team.
- **Consumers**: All higher-level business capabilities.
- **Dependencies**: Memory, Storage.
- **Future evolution**: Serverless edge execution.

### Guardian
- **Purpose**: Universal security policy enforcement.
- **Responsibilities**: Action interception, RBAC evaluation.
- **Owner**: Security Architecture Team.
- **Consumers**: Runtime, API.
- **Dependencies**: Configuration, Identity.
- **Future evolution**: Real-time behavioral threat blocking.

### Workflow
- **Purpose**: Stateful DAG orchestration.
- **Responsibilities**: Pause/resume, step execution, parallel routing.
- **Owner**: Orchestration Team.
- **Consumers**: Agents, API.
- **Dependencies**: Memory, Task.
- **Future evolution**: Multi-cluster workflow dispatch.

### Agents
- **Purpose**: Autonomous decision execution.
- **Responsibilities**: Goal evaluation, tool selection.
- **Owner**: Autonomous Systems Team.
- **Consumers**: Workflow, Presentation.
- **Dependencies**: Skills, Memory, Providers.
- **Future evolution**: Multi-agent adversarial reasoning.

### Knowledge
- **Purpose**: Long-term semantic data retrieval.
- **Responsibilities**: Vector search, document chunking.
- **Owner**: Data Systems Team.
- **Consumers**: Agents, Runtime.
- **Dependencies**: Storage, Providers.
- **Future evolution**: Real-time multimodal ingestion.

### Memory
- **Purpose**: Episodic context persistence.
- **Responsibilities**: Context window tracking, summarization.
- **Owner**: State Management Team.
- **Consumers**: Agents, Workflow.
- **Dependencies**: Storage.
- **Future evolution**: Automatic context compression.

### Skills
- **Purpose**: Discrete agent capabilities.
- **Responsibilities**: Tool execution, input validation.
- **Owner**: Integration Team.
- **Consumers**: Agents.
- **Dependencies**: Connectors.
- **Future evolution**: Dynamic WASM skill execution.

### Providers
- **Purpose**: Abstract AI and service interfaces.
- **Responsibilities**: Fulfilling intelligence and notification requests.
- **Owner**: Platform Integration Team.
- **Consumers**: Agents, Knowledge, Guardian.
- **Dependencies**: Infrastructure.
- **Future evolution**: Automated model failover routing.

### Connectors
- **Purpose**: External system adapters.
- **Responsibilities**: Protocol translation.
- **Owner**: Integration Team.
- **Consumers**: Skills.
- **Dependencies**: Providers.
- **Future evolution**: No-code connector generation.

### Storage
- **Purpose**: Data persistence abstraction.
- **Responsibilities**: Blob and document saving.
- **Owner**: Data Systems Team.
- **Consumers**: Knowledge, Memory.
- **Dependencies**: Infrastructure.
- **Future evolution**: Automated cold storage archiving.

### Monitoring
- **Purpose**: Real-time system observation.
- **Responsibilities**: Exposing health metrics.
- **Owner**: Site Reliability Team.
- **Consumers**: Operations.
- **Dependencies**: Runtime.
- **Future evolution**: AI-driven anomaly alerting.

### Audit
- **Purpose**: Immutable ledger logging.
- **Responsibilities**: Recording policy decisions.
- **Owner**: Compliance Team.
- **Consumers**: Governance.
- **Dependencies**: Storage.
- **Future evolution**: Cryptographic ledger verification.

### Licensing
- **Purpose**: Capability entitlement enforcement.
- **Responsibilities**: Validating usage tiers.
- **Owner**: Platform Architecture Team.
- **Consumers**: Runtime, Guardian.
- **Dependencies**: Organization.
- **Future evolution**: Usage-based token billing.

### Configuration
- **Purpose**: Structural settings schemas.
- **Responsibilities**: Type-safe environment variable mapping.
- **Owner**: Core Engineering Team.
- **Consumers**: All subsystems.
- **Dependencies**: None.
- **Future evolution**: Dynamic remote config updates.

### Database
- **Purpose**: Relational state.
- **Responsibilities**: Acid transactions.
- **Owner**: Data Systems Team.
- **Consumers**: Organization, Workspace.
- **Dependencies**: Infrastructure.
- **Future evolution**: Active-active multi-region clustering.

### Cache
- **Purpose**: Ephemeral fast access.
- **Responsibilities**: Storing volatile state.
- **Owner**: Data Systems Team.
- **Consumers**: Runtime, Guardian.
- **Dependencies**: Infrastructure.
- **Future evolution**: Predictive cache warming.

### Queue
- **Purpose**: Asynchronous task buffer.
- **Responsibilities**: Decoupling producers and consumers.
- **Owner**: Orchestration Team.
- **Consumers**: Workflow, Agents.
- **Dependencies**: Infrastructure.
- **Future evolution**: Priority-based dead letter recovery.

---

## Bounded Context Map

### Identity & Access Context
- **Purpose**: Manages who can access what.
- **Ownership**: Security Architecture.
- **Responsibilities**: Authentication, token lifecycle, role mapping.
- **Public interfaces**: `verifyToken`, `resolveRole`.
- **Upstream contexts**: None.
- **Downstream contexts**: Guardian Context.
- **Communication rules**: Synchronous for authentication, asynchronous for audit.
- **Isolation rules**: Never stores application business state.
- **Shared kernel rules**: Shares only abstract opaque types (`UserId`, `Token`).
- **Context boundaries**: Stops strictly at identity resolution; does not evaluate business policy.

### Orchestration Context
- **Purpose**: Manages execution state and progression.
- **Ownership**: Orchestration Team.
- **Responsibilities**: DAG execution, state transitions.
- **Public interfaces**: `startWorkflow`, `resumeWorkflow`.
- **Upstream contexts**: Presentation Context.
- **Downstream contexts**: Agent Context, Memory Context.
- **Communication rules**: Strictly asynchronous state transitions.
- **Isolation rules**: Cannot execute agent logic directly.
- **Shared kernel rules**: Shares `WorkflowId` and `CorrelationId`.
- **Context boundaries**: Delegates all intelligence processing to Agent Context.

### Agent Context
- **Purpose**: Manages autonomous intelligence.
- **Ownership**: Autonomous Systems.
- **Responsibilities**: Reasoning, tool selection.
- **Public interfaces**: `executeTask`, `evaluateGoal`.
- **Upstream contexts**: Orchestration Context.
- **Downstream contexts**: Provider Context, Skill Context.
- **Communication rules**: Bidirectional asynchronous with Workflow.
- **Isolation rules**: Cannot access raw database tables.
- **Shared kernel rules**: Shares abstract `Prompt` and `ToolSchema` contracts.
- **Context boundaries**: Acts strictly upon provided context; cannot spontaneously initiate workflows.

### Provider Context
- **Purpose**: Abstracts external capabilities.
- **Ownership**: Platform Integration.
- **Responsibilities**: Executing AI models, dispatching notifications.
- **Public interfaces**: `generateText`, `generateEmbedding`.
- **Upstream contexts**: Agent Context, Knowledge Context.
- **Downstream contexts**: External Infrastructure.
- **Communication rules**: Synchronous via circuit breakers.
- **Isolation rules**: Completely ignorant of platform business logic.
- **Shared kernel rules**: Shares generic `ModelRequest` contracts.
- **Context boundaries**: Operates as a stateless facade.

---

## Module Responsibility Matrix

| Module | Purpose | Inputs | Outputs | Owner | Dependencies | Consumers | Architectural Boundaries |
|--------|---------|--------|---------|-------|--------------|-----------|--------------------------|
| **API** | Boundary routing | HTTP Requests | HTTP Responses | Integration | Contracts | External Clients | Edge ingress only |
| **Runtime** | Engine loop | Config | Active State | Core | Memory | API, Agent | Orchestration layer |
| **Guardian** | Policy enforcement | Actor, Action | Allow/Deny | Security | Identity | All layers | Pre-execution interceptor |
| **Workflow** | State machine | Trigger | Result | Orchestration | Memory | API | State management only |
| **Agent** | Reasoning | Context, Goal | Action | Autonomous | Skills, Providers | Workflow | Abstract intelligence |
| **Knowledge** | Semantic search | Query | Vector matches | Data Systems | Storage | Agent | Data retrieval only |

---

## Package Dependency Matrix

### Lowest Layer ↓ Highest Layer
1. `@aegis/types` (Lowest)
2. `@aegis/contracts`
3. `@aegis/config`
4. `@aegis/shared`
5. `@aegis/providers`
6. `@aegis/guardian`
7. `@aegis/knowledge`
8. `@aegis/memory`
9. `@aegis/agents`
10. `@aegis/workflow`
11. `@aegis/runtime` (Highest)

### Dependency Rules
- **Allowed dependencies**: Higher layers may import from strictly lower layers.
- **Forbidden dependencies**: Lower layers must NEVER import from higher layers.
- **Dependency direction**: Unidirectional, pointing downward toward stability.
- **Layer isolation**: Business logic (`@aegis/agents`) cannot depend on infrastructural specifics (`@aegis/providers/aws`).
- **Circular dependency prevention**: Enforced strictly via structural tooling (e.g., madge); build fails if a cycle is introduced.
- **Package ownership**: Modifications to base layers (`types`, `contracts`) require architectural sign-off.

---

## Runtime State Machines

### Runtime State Machine
- **Initial state**: `BOOTING`
- **Intermediate states**: `CONFIGURING`, `CONNECTING`, `READY`
- **Failure states**: `BOOT_FAILED`, `CRASHED`
- **Recovery states**: `RESTARTING`
- **Terminal states**: `SHUTDOWN`
- **Allowed transitions**: `BOOTING -> CONFIGURING`, `READY -> SHUTDOWN`
- **Forbidden transitions**: `CRASHED -> READY` (Must restart)

### Workflow State Machine
- **Initial state**: `PENDING`
- **Intermediate states**: `RUNNING`, `PAUSED`, `WAITING_FOR_INPUT`
- **Failure states**: `FAILED`, `TIMED_OUT`
- **Recovery states**: `RETrying`
- **Terminal states**: `COMPLETED`, `CANCELLED`
- **Allowed transitions**: `RUNNING -> PAUSED`, `PAUSED -> RUNNING`
- **Forbidden transitions**: `COMPLETED -> RUNNING`

### Agent State Machine
- **Initial state**: `IDLE`
- **Intermediate states**: `THINKING`, `ACTING`, `OBSERVING`
- **Failure states**: `ERROR`, `HALTED`
- **Recovery states**: `REPLANNING`
- **Terminal states**: `GOAL_MET`, `GOAL_FAILED`
- **Allowed transitions**: `THINKING -> ACTING`, `ACTING -> OBSERVING`
- **Forbidden transitions**: `IDLE -> ACTING` (Must think first)

---

## AI Execution Pipeline

### Intent
The raw user request or system trigger is received.
↓
### Planning
The Orchestrator determines the required workflow graph.
↓
### Guardian
Authorization is checked against the actor's intent and target data.
↓
### Memory
Recent episodic context is retrieved for the assigned Agent.
↓
### Knowledge
Semantic search fetches relevant long-term documents based on intent.
↓
### Prompt Assembly
System instructions, Memory, Knowledge, and constraints are compiled into a structural prompt.
↓
### Provider
The abstract Provider layer communicates with the AI model.
↓
### Tool Calling
The model decides to invoke a Skill. Execution halts while the Skill runs.
↓
### Validation
The Skill output is validated against strict schema contracts.
↓
### Memory Update
The outcome of the thought and action is appended to the episodic state.
↓
### Knowledge Update
(Optional) New insights are vectorized and stored.
↓
### Audit
The entire decision tree and outcome is logged immutably.
↓
### Response
The final serialized outcome is returned to the consumer.

---

## Prompt Lifecycle

1. **Prompt Creation**: Base structural templates are selected based on the Agent Persona.
2. **Prompt Enrichment**: Formatting rules and output schemas are appended.
3. **Context Injection**: The immediate user query is sanitized and injected.
4. **Memory Injection**: The rolling window of past interactions is serialized and added.
5. **Knowledge Injection**: RAG (Retrieval-Augmented Generation) results are appended as factual context.
6. **Policy Validation**: The finalized prompt is scanned for prompt injection or policy violations.
7. **Provider Execution**: The payload is mapped to provider-specific structures (e.g., OpenAI vs. Anthropic).
8. **Response Processing**: The raw text/JSON is parsed and strictly validated.
9. **Audit**: The input prompt and output completion are hashed and stored for accountability.
10. **Cleanup**: Ephemeral prompt variables are garbage collected from memory.

---

## Plugin Architecture

### Plugins
- **Purpose**: Expand platform capabilities without core modification.
- **Responsibilities**: Registering new extensions during boot.
- **Lifecycle**: Loaded at runtime via reflection or registry maps.
- **Extension Rules**: Must conform to strict `@aegis/contracts` interfaces.

### Skills
- **Purpose**: Expose specific actions to Agents.
- **Isolation**: Execute in sandboxed processes or limited-permission scopes.

### Providers
- **Purpose**: Connect to new LLMs or Cloud APIs.
- **Ownership**: Community or Platform Integration teams.

### Adapters
- **Purpose**: Translate proprietary external data into Aegis standard types.
- **Lifecycle**: Bound to the request scope.

---

## Architecture Constraints

### Runtime must never directly access database.
- **Why**: Enforces bounded contexts. Database access must funnel through repositories to ensure audit and policy hooks are triggered.

### Guardian must never call providers.
- **Why**: Security evaluation must be deterministic, instantaneous, and strictly local. Network calls introduce unacceptable latency and failure vectors into the security path.

### Contracts must never contain business logic.
- **Why**: Contracts define *what*, not *how*. Including logic creates coupling and prevents pure structural sharing.

### Types must never contain runtime logic.
- **Why**: Types are compile-time constructs. Adding runtime validators (like Zod schemas) into pure type packages violates layer boundaries.

### Shared must never import business packages.
- **Why**: `shared` is universal. Importing business logic creates immediate circular dependencies and pollutes the global scope.

### Config must never read environment variables.
- **Why**: Configuration defines structural payload expectations. The actual reading of `process.env` is a runtime responsibility, ensuring configuration definitions remain purely structural.

---

## Architecture Anti-Patterns

### Circular Dependencies
- **Problem**: Package A depends on Package B, which depends on Package A.
- **Impact**: Breaks build systems, creates memory leaks, and prevents package isolation.
- **Required correction**: Extract the shared dependency into a lower-level contract or type package.

### Business Logic inside Contracts
- **Problem**: Implementing validation or transformation inside an interface package.
- **Impact**: Forces consumers of the contract to inherit runtime dependencies they do not need.
- **Required correction**: Move logic to implementations, keep contracts purely structural.

### Tight Coupling
- **Problem**: Modules directly instantiating concrete classes of other modules.
- **Impact**: Prevents mocking during tests and destroys modularity.
- **Required correction**: Utilize Dependency Injection and code against interfaces.

### Global Singleton Abuse
- **Problem**: Using mutable global state accessible from anywhere.
- **Impact**: Makes tests non-deterministic and creates race conditions in concurrent execution.
- **Required correction**: Pass context explicitly through dependency injection or request scope.

---

## Approved Design Patterns

### Repository Pattern
- **Purpose**: Abstract data persistence.
- **When to use**: Whenever interacting with the database or file system.
- **Benefits**: Allows swapping underlying database technologies without impacting business logic.

### Dependency Injection
- **Purpose**: Supply dependencies to an object rather than creating them internally.
- **When to use**: For all service, provider, and engine instantiation.
- **Benefits**: Enables absolute testability via mock injection.

### Outbox Pattern
- **Purpose**: Guarantee at-least-once message delivery.
- **When to use**: When updating local database state and publishing an event to a queue simultaneously.
- **Benefits**: Prevents dual-write inconsistencies.

### Saga Pattern
- **Purpose**: Manage distributed transactions.
- **When to use**: For cross-boundary workflows (e.g., Billing + Provisioning).
- **Benefits**: Avoids locking resources across network boundaries using compensating transactions.

---

## Operational Architecture

### Scalability Strategy
The platform scales purely horizontally. All state is externalized to Cache (Redis) and Database (PostgreSQL).

### Capacity Planning
Compute is autoscaled based on queue depth and memory pressure, not CPU utilization, to account for asynchronous IO blocking during LLM inference.

### SLO (Service Level Objectives)
- **API Latency**: 99th percentile < 200ms (excluding Provider inference time).
- **Provider Latency**: Abstracted, but system overhead < 50ms.

### Graceful Degradation
If Knowledge Engine fails, Agents fall back to purely reactive reasoning. If caching fails, system falls back to database with increased latency.

### Load Shedding
When systemic capacity is breached, the API boundary aggressively rejects new synchronous requests with HTTP 429, prioritizing in-flight workflow completion.

---

## Documentation Governance

### Document ownership
Every architectural document is owned by the Chief Software Architect. Implementation docs are owned by package maintainers.

### Review workflow
All documentation changes require a Pull Request, automatic linting for broken links, and manual peer review.

### Approval workflow
Changes to the Platform Blueprint require formal Architecture Review Board (ARB) consensus.

### ADR lifecycle
1. **Draft**: Proposed but not accepted.
2. **Accepted**: Approved for implementation.
3. **Deprecated**: Superseded by a newer ADR.

---

## Architecture Evolution

### How architecture evolves
Evolution is strictly additive. The system grows by adding new capability layers or extending contracts, rather than rewriting core paths.

### How new modules are introduced
New modules must be proposed via an ADR, defining their place in the Package Dependency Matrix and Bounded Context Map before any code is written.

### How breaking architecture changes are approved
Breaking changes require a major version bump and a migration pathway document approved by the ARB.

### How future platform capabilities are added
Capabilities like novel AI reasoning patterns or multi-agent swarms are added via the Plugin and Skill architecture, ensuring the core Runtime remains undisturbed.
