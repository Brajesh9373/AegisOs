# AegisAI Database Architecture

This document defines the high-level database architecture and foundational data standards for AegisAI. It is not a database schema; it governs the architectural principles that any future schema must follow.

## Objectives
The database architecture is designed to logically organize and persist data across the platform. It must inherently support:
* Enterprise organizations operating in isolated or shared multi-tenant modes.
* Strict human ownership and accountability over all assets.
* Secure and governed AI assistant data and configuration.
* End-to-end governance and policy enforcement.
* Comprehensive and immutable auditing.
* Explicit versioning of critical system objects.
* Long-term scalability and security.

## Database Philosophy
* **Single Source of Truth**: Data is never duplicated across domains; relationships are always explicit.
* **Everything is Versioned**: Core operational assets maintain a strict historical record of state changes.
* **Nothing is Permanently Deleted**: Soft deletion and archival are the default strategies to preserve referential integrity and audit trails.
* **Everything is Auditable**: Every mutation generates an immutable ledger entry.
* **Organization-First Design**: All business data is structurally bound to a specific organization.
* **No Duplicated Business Data**: Configuration and knowledge are normalized to prevent drift.

## Data Domains
The platform's data is logically segregated into distinct domains, each holding specific responsibilities:
* **Identity**: Manages authentication profiles, credentials, and identity provider mappings.
* **Organizations**: The root domain for multi-tenant isolation, storing tenant metadata and global boundaries.
* **Departments**: Logical subdivisions within an organization for compartmentalized knowledge and policy.
* **Users**: Human operators, their profiles, preferences, and organization associations.
* **RBAC**: Roles, permissions, scopes, and their assignments to users and agents.
* **Agents**: Configurations, instructions, limits, and persona definitions for AI workforces.
* **Skills**: Registries of executable capabilities, tool configurations, and integration definitions.
* **Knowledge**: Pointers to organizational context, documents, and standard operating procedures.
* **Memory**: The contextual history, conversation threads, and learned state of agents over time.
* **Tasks**: Definitions, queues, state tracking, and outcomes for asynchronous workflows.
* **Runtime**: Telemetry, execution states, and provider routing rules.
* **Guardian**: Policies, security boundaries, and intervention rules governing execution.
* **Approvals**: Requests, statuses, and human-in-the-loop decisions for sensitive actions.
* **Notifications**: Templates, routing rules, and delivery states for alerts.
* **Audit**: The immutable, append-only ledger of all system and user activity.
* **Licensing**: Feature entitlements, limits, and self-hosted instance validation.
* **Settings**: Global, organizational, and user-level configuration overrides.
* **Monitoring**: High-level health metrics, agent performance aggregations, and usage tracking.

## Ownership Rules
Ownership is absolute and strictly enforced at the data level:
* **Users own Agents**: An agent's actions are fundamentally tied to the human who owns or commands it.
* **Organizations own Knowledge and Memory**: Enterprise data never belongs to a specific user or AI.
* **Departments own Operational Data**: Workflows and department-specific policies belong to the department.
* **Transferability**: Ownership can be transferred, but only by Administrators with explicitly logged approval.
* **AI Ownership**: AI agents do not own data. They act as delegates with temporary, strictly scoped access to organization or user data.

## Data Lifecycle
The lifecycle of all platform data is strictly controlled:
* **Creation**: Requires authenticated identity and explicit authorization.
* **Modification**: Replaces the current active state, but preserves the previous state in history if versioned.
* **Versioning**: Major assets spawn a new immutable version upon modification.
* **Archiving**: Data moved out of active query paths but preserved for compliance.
* **Transfer**: Modifies the ownership boundary while logging the exact transfer event.
* **Deletion (Soft)**: Marks the record as inactive, removing it from active queries without destroying the underlying data.
* **Recovery**: Reversing a soft delete to restore the asset to active duty.
* **Audit**: Every stage of this lifecycle is permanently recorded.

## Versioning Strategy
Core objects must support explicit versioning to guarantee operational safety and rollback capabilities. This includes:
* **Skills**: Prevents breaking changes in active workflows when a tool is updated.
* **Agents**: Preserves the behavioral configuration of an AI at a specific point in time.
* **Policies**: Ensures historical audits can verify which exact policy was active when a decision was made.
* **Knowledge**: Tracks updates to SOPs and organizational context.
* **Memory**: Versioned to track how an agent's understanding evolves.
* **Prompts**: Versioned to allow A/B testing and rollback if AI performance degrades.
* **Configurations**: Prevents system-breaking changes from causing permanent outages.

## Soft Delete Policy
Permanent deletion (hard delete) is strictly avoided for all business data.
* **Archival**: Data is tombstoned (soft-deleted) and excluded from standard application queries.
* **Recovery**: Soft-deleted data can be fully restored by authorized administrators.
* **Retention**: Data is kept indefinitely unless a strict compliance policy (e.g., GDPR right to be forgotten) legally mandates a hard purge via a specialized secure process.
* **Audit Preservation**: Hard deleting data would break historical audit trails. Soft deletes ensure the context of past actions remains perfectly intact.

## Multi-Tenant Strategy
AegisAI supports multi-organization isolation securely:
* **Isolation**: Organization IDs are embedded into the root of every business data domain. All queries implicitly filter by Organization.
* **Protection**: Cross-organization data bleeding is structurally impossible at the database access layer.
* **Platform Data vs. Organization Data**: Global platform configurations (e.g., system-wide certified Skills) are stored completely separately from Organization-owned customized data.

## Security
* **Least Privilege**: The application layer accesses the database using roles strictly limited to required operations.
* **Encryption**: Sensitive fields (tokens, provider keys, PII) are encrypted at rest using AES-256.
* **Secret Isolation**: Secrets are stored in isolated, highly restricted domains, never returned in standard read queries.
* **Audit Logging**: Data mutations must guarantee an accompanying audit write.
* **No Direct Access**: End-users, UIs, and external systems never connect directly to the database.
* **Permission Validation**: Database operations are aborted if the application layer fails to provide a valid permission context.

## Data Integrity
* **Consistency**: Strong consistency is required for all RBAC, Ownership, and Guardian operations.
* **Transactions**: Multi-domain mutations must be wrapped in ACID-compliant transactions to prevent partial states.
* **Validation**: The database layer enforces constraints (uniqueness, non-nullability) as a final defense against application bugs.
* **Ownership Validation**: Foreign keys ensure that relationships cannot cross unauthorized boundaries.
* **Relationship Integrity**: No orphaned records are permitted; soft-deletes must gracefully handle dependent children.

## Performance Principles
* **Scalability**: The design must support horizontal scaling, utilizing read-replicas for heavy query loads.
* **Partitioning**: Massive tables (e.g., Audit, Memory, Tasks) must be designed for time-based or organization-based partitioning.
* **Caching**: Highly accessed, infrequently changing data (RBAC, Settings) should be cache-friendly.
* **Search Strategy**: Full-text and vector searches are offloaded to specialized indices, not forced onto transactional tables.
* **Read vs Write Optimization**: Transactional tables are optimized for rapid writes and exact reads, while analytical queries are deferred to replicas.

## Migration Principles
* **Backward Compatibility**: Database migrations must never break running versions of the application.
* **Migration Strategy**: Changes follow an expand-and-contract model (add new schema, migrate data, remove old schema in later release).
* **Versioning**: Schema versions are strictly tracked.
* **Rollback**: Every migration must have a tested, safe rollback mechanism.
* **Zero Data Loss**: Migrations must never destructively truncate or drop business data without a mandated archival step.

## Database Constraints
The following permanent rules govern database interactions:
* Never bypass ownership checks in queries.
* Never bypass the audit ledger for state mutations.
* Never hard delete business data.
* Never duplicate user identity across organizations.
* Never allow inconsistent relationships or orphaned references.
* Never store API keys, tokens, or passwords in plain text.
* Never break existing data contracts without a versioned migration.

## Final Principles
The AegisAI database architecture must always prioritize:
**Integrity**
**Security**
**Governance**
**Auditability**
**Scalability**
**Maintainability**
**Enterprise Reliability**
