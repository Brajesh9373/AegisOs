# AegisOS Security Architecture

This document describes the security controls implemented in the AegisOS platform. Every statement is derived from the production source code.

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Authorization](#2-authorization)
3. [Agent Governance](#3-agent-governance)
4. [Tenant Isolation](#4-tenant-isolation)
5. [Secret Handling](#5-secret-handling)
6. [API Security](#6-api-security)
7. [Container Security](#7-container-security)
8. [Network Security](#8-network-security)
9. [Data Protection](#9-data-protection)
10. [Audit Trail](#10-audit-trail)
11. [Policy Recommendations](#11-policy-recommendations)

---

## 1. Authentication

### 1.1 JWT Token Flow

The platform uses a dual-token scheme implemented in `JwtAuthenticationService` and `JwtTokenCodec`.

- **Access tokens** are short-lived (default 15 minutes). They carry the subject, roles, scopes, tenant ID, principal type, a unique JTI, and standard JWT claims (iss, aud, iat, exp).
- **Refresh tokens** are longer-lived (default 24 hours). They carry the same identity payload but with `token_type=refresh`.
- Tokens are signed with HS256 using rotating symmetric keys. Each key is identified by a `kid` header. Old keys remain valid for verification after rotation, enabling zero-downtime key rollover.
- The token payload includes `sub`, `type`, `ptype` (user or service), `roles`, `scopes`, `tenant`, `iat`, `exp`, `jti`, `iss`, and `aud`.

### 1.2 Login

The `/api/v1/auth/login` endpoint accepts email and password, returns an access/refresh token pair with `token_type=bearer` and `expires_in` (seconds until the access token expires). The refresh token is opaque to the client and used solely at the refresh endpoint.

### 1.3 Token Refresh

The `/api/v1/auth/refresh` endpoint validates the supplied refresh token, checks that it has not been revoked, verifies its type is `REFRESH`, revokes the old refresh token (one-time use), and issues a fresh token pair. This is a token rotation -- each refresh token can only be used once.

### 1.4 Logout and Revocation

The `/api/v1/auth/logout` endpoint extracts the Bearer token from the `Authorization` header and adds its JTI to an in-memory revocation set. All subsequent verification calls check the revocation set before accepting a token. The `revoke` method silently ignores invalid tokens to prevent information leakage.

### 1.5 Password Hashing

Passwords are hashed with bcrypt via `BcryptPasswordHasher`. The `hash` method generates a salted bcrypt hash. The `verify` method uses `bcrypt.checkpw` in a try/except that returns `False` on any `ValueError`, preventing timing or error-based side channels.

### 1.6 API Key Management

`ApiKeyManager` generates API keys with the format `ecms_<token_urlsafe(32)>`. Only the SHA-256 hash of the key is stored. Verification uses `constant_time_compare` (an HMAC-based comparison from `hmac.compare_digest`) to mitigate timing attacks.

---

## 2. Authorization

### 2.1 Policy Evaluation Engine

Authorization is implemented as a dual-layer system: RBAC role grants combined with ABAC policy rules.

**Evaluation order** (in `PolicyAuthorizationService._evaluate`):

1. Explicit DENY policies are evaluated first. Any match results in immediate denial.
2. Explicit ALLOW policies are evaluated next. The first match grants access.
3. Role-based permissions are checked: the required `resource:action` string is matched against the agent's registered role permissions, including wildcard patterns (`resource:*` and `*:*`).
4. If no policy or role matches, access is denied (default-deny / least privilege).

### 2.2 AccessPolicy Model

Policies are stored as database rows (`access_policies` table) and evaluated at query time. Each policy carries:

- **Subject matching**: `agent_id` (exact), `department` (exact), `role_level_min` (minimum role level).
- **Resource matching**: `resource_type` (memory_atom, graph_node, file, or all), `path_pattern` (glob via `fnmatch`), `source_type` (git, mysql, jira, or all), `resource_attrs` (arbitrary JSON key-value pairs).
- **Action**: `read`, `write`, `delete`, or `*`.
- **Effect**: `allow` or `deny`.
- **Priority**: integer for ordering (lower = higher priority).

Root agents (those with `reports_to IS NULL`) bypass all policy checks and receive unrestricted access.

### 2.3 Domain Authorization Model

The authorization domain (`auth.domain.authorization`) defines:

- `Role` -- a named role with a list of `resource:action` permission strings.
- `Policy` -- an ABAC-ready policy with effect, resource, action, roles, subjects, and conditions.
- `AccessRequest` -- captures the subject, roles, resource, action, and arbitrary attributes for evaluation.
- `AccessDecision` -- the outcome: `allowed` (bool), `reason` (string), and optional `matched_policy` ID.

### 2.4 Knowledge Access

The `knowledge_access` method on `PolicyAuthorizationService` controls access to knowledge objects. A principal is granted access if their subject is in the policy's `allowed_principals` list, if any of their roles are in `allowed_roles`, or if the resource classification is `PUBLIC`.

### 2.5 Query-Time Filtering

The access engine (`agent.access_engine`) provides async post-filtering for both memory atom search results and graph query results. Every result set returned by `search_memory` or `query_graph` is filtered through the active policy set for the requesting agent before being returned.

---

## 3. Agent Governance

### 3.1 Hierarchy

Agents form a self-referential hierarchy via the `reports_to` foreign key. The CTO agent (`reports_to IS NULL`) is the root. All other agents report to a parent. The hierarchy governs delegation authority and access bypass.

### 3.2 Governance Assignments

The `ProjectAgentGovernanceAssignment` model links permanent organization members to project-scoped runtime agents with a defined responsibility:

- **primary_owner**: the single accountable human for an agent. Enforced as unique per agent -- a new primary owner assignment fails if one already exists.
- **monitor**: a human who observes an agent's behavior.
- **approver**: a human who must approve an agent's actions.

Assignments carry a lifecycle: `active`, `needs_review`, or `revoked`. A unique constraint prevents duplicate (member, agent, responsibility) tuples.

### 3.3 Tool Policy

Each agent carries a `tool_policy` JSON field on the `Agent` model. The format is:

```json
{"blocked_tools": ["kill_shell", "web_search"], "allowed_tools": ["*"]}
```

If `allowed_tools` contains `"*"`, all non-blocked tools are available. If it is an explicit list, only those tools are available. `blocked_tools` always takes precedence. The `get_effective_tools_for_agent` function filters the full tool registry at runtime.

### 3.4 Workspace Scope

Each agent carries a `workspace_scope` JSON field defining read/write path patterns (e.g., `{"write": "/workspace/**", "read": "/**"}`). The CTO defaults to full read/write access.

### 3.5 Delegation Enforcement

The `can_assign` function walks the `reports_to` chain to verify that an assigner is a manager (direct or indirect) of the assignee. An agent cannot assign tasks to themselves. Cross-team requests (`can_request_cross_team`) require the requester to have direct reports and the target department to contain at least one agent.

---

## 4. Tenant Isolation

### 4.1 Organization Scoping

The `organization_id` column is present on all multi-tenant tables: `AggregateRecord`, `ConnectorIngestionJob`, `ConnectorIngestionPartition`, `KnowledgeGraphSnapshot`, and their associated repositories. Every query that touches these tables filters by `organization_id`.

### 4.2 Provenance Constraints

Database migrations enforce provenance through composite unique constraints and foreign keys scoped to `organization_id`. For example, connector ingestion partitions are uniquely constrained on `(id, job_id, organization_id)`, and foreign keys reference the parent table's `(id, organization_id)` pair. This prevents cross-tenant data references at the database level.

### 4.3 Identity Tenant Binding

The `Identity` model carries an optional `tenant_id`. JWT tokens encode the tenant ID in the `tenant` claim. The authorization service passes tenant context through the evaluation chain.

---

## 5. Secret Handling

### 5.1 Credentials Never Persisted

API keys are stored only as SHA-256 hashes. The raw key is returned once at generation time and never stored. Passwords are stored as bcrypt hashes with per-password salts.

### 5.2 Git Credential Redaction

Git operations pass credentials through process environment variables (`GIT_CONFIG_KEY_0=http.extraHeader`), never through URLs, command arguments, or error output. The `_redact_git_error` function strips URL credentials and query parameters from Git diagnostic output using regex substitution before it is included in error messages.

### 5.3 Sensitive Value Redaction

The `redaction` module defines `SENSITIVE_KEYS` -- a frozen set of substrings (`password`, `secret`, `token`, `api_key`, `authorization`, `credential`, etc.) that mark mapping keys as sensitive. The `redact_mapping` function recursively replaces matching values with `***REDACTED***`. The `redact` function discards its argument entirely and returns the redaction marker.

### 5.4 Constant-Time Comparison

The `constant_time_compare` function wraps `hmac.compare_digest` to prevent timing-based side-channel attacks when comparing tokens, hashes, or signatures.

### 5.5 Environment Variable Configuration

All secrets (database passwords, S3 keys, API keys, Grafana admin password) are injected through environment variables at deployment time. The production `docker-compose.prod.yml` uses `${VAR:?error message}` syntax to enforce that required secrets are provided. No secrets are hardcoded in source or committed to version control.

### 5.6 Encryption Service

The `EncryptionService` provides AES-256-GCM authenticated encryption for credentials, secrets, and PII. Ciphertext is self-describing: a 12-byte random nonce is prepended to the ciphertext and the whole thing is base64-encoded. Keys can be rotated in-place; old ciphertext remains decryptable if the old key is retained.

---

## 6. API Security

### 6.1 Rate Limiting

`RateLimitMiddleware` implements a fixed-window, per-client rate limiter. The default limit is 1000 requests per 60-second window. Clients exceeding the limit receive HTTP 429 with `{"error": "rate_limited", "message": "Too many requests"}`. The client is identified by `request.client.host`.

### 6.2 CORS

CORS is configured through `CORSMiddleware` with explicit origin lists from `ECMS_CORS_ALLOW_ORIGINS`. In development, localhost origins are allowed. In production, only explicitly configured origins are permitted. Credentials are allowed by default (`cors_allow_credentials=true`).

### 6.3 Request Context and Correlation IDs

`RequestContextMiddleware` binds a correlation ID and a unique request ID to the ambient context for every incoming request. If the client supplies an `X-Correlation-ID` header, it is preserved; otherwise a new one is generated. The correlation ID is echoed back on every response, enabling end-to-end request tracing across distributed services.

### 6.4 Observability Middleware

- `MetricsMiddleware` records request count, method, path, status code, and latency for every request via `MetricsRegistry`.
- `TracingMiddleware` wraps each request in an OpenTelemetry span (`{METHOD} {path}`), enabling distributed trace collection.

### 6.5 Compression

`GZipMiddleware` compresses responses larger than 500 bytes.

---

## 7. Container Security

### 7.1 Non-Root Execution

The backend Dockerfile creates a dedicated `ecms` user with UID 1000:

```dockerfile
RUN useradd --create-home --uid 1000 ecms
```

All workspace and data directories are `chown`ed to `ecms:ecms`. The `USER ecms` directive switches to this user before the entrypoint runs. The application never runs as root.

### 7.2 Kubernetes Security Context

The Kubernetes deployment manifest enforces:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
```

This is a pod-level constraint that prevents the container from running as root even if the image is modified.

### 7.3 Resource Limits

Every container declares CPU and memory limits. The connector ingestion worker, for example, is capped at 0.75 CPU / 2GB RAM; the graph writer at 0.5 CPU / 1GB RAM. The backend deployment requests 100m CPU / 256Mi RAM and limits at 1 CPU / 512Mi RAM.

### 7.4 Graceful Shutdown

The backend deployment specifies `terminationGracePeriodSeconds: 30` and a `preStop` lifecycle hook (`sleep 5`) to allow in-flight requests and connections to drain before the container is terminated.

### 7.5 Health Checks

Liveness and readiness probes are defined for all services. The backend uses `/health` (liveness) and `/ready` (readiness) endpoints. Connector workers use dedicated health check modules. PostgreSQL, Redis, FalkorDB, MinIO, and other dependencies all have their own health checks.

---

## 8. Network Security

### 8.1 Internal-Only Services

In production, internal services (PostgreSQL, Redis, FalkorDB, Qdrant, MinIO, Prometheus, Loki, Tempo) are not exposed to the host. They communicate over an internal Docker bridge network (`ecms-network`). Only the frontend (port 3000) and Grafana (bound to `127.0.0.1:3300`) are exposed externally.

### 8.2 Digest-Pinned Images

The production `docker-compose.prod.yml` requires digest-pinned images for all third-party dependencies. Environment variables use the `:?` error syntax:

```yaml
image: ${FALKORDB_IMAGE:?Use a digest-pinned FalkorDB image}
image: ${QDRANT_IMAGE:?Use a digest-pinned Qdrant image}
image: ${MINIO_IMAGE:?Use a digest-pinned MinIO image}
image: ${PROMETHEUS_IMAGE:?Use a digest-pinned Prometheus image}
```

The compose file will refuse to start if these variables are not set, preventing supply-chain attacks through mutable image tags.

### 8.3 Grafana Authentication

Grafana disables anonymous access (`GF_AUTH_ANONYMOUS_ENABLED=false`) and requires explicit admin credentials via environment variables.

---

## 9. Data Protection

### 9.1 Encrypted Configuration

The `EncryptionService` provides AES-256-GCM encryption for sensitive configuration values. The service supports key rotation -- calling `rotate_key` replaces the active key while returning it for external storage. Old keys can be retained to decrypt legacy ciphertext.

### 9.2 Error Truncation

Git command errors are truncated to 2000 characters before inclusion in exceptions. Tool result summaries are truncated to 300 characters for memory atom capture. File read results are truncated to 4000 characters.

### 9.3 Credential Redaction from Git Output

The `_redact_git_error` function in `git_runtime.py` strips embedded credentials from Git error messages using a regex that matches `https://user:pass@host` patterns and replaces them with `https://host/[REDACTED]`.

### 9.4 Production Safety Validators

The `AppSettings` model includes a `reject_production_chaos_delay` validator that raises a `ValueError` if the qualification-only build delay is nonzero in the production profile, preventing test-only behavior from reaching production.

---

## 10. Audit Trail

### 10.1 AuditRecord

The `AuditRecord` model (`audit_records` table) is an immutable log entry recording:

- `actor`: the principal who performed the action (indexed).
- `action`: what was done (indexed).
- `resource`: the target resource.
- `outcome`: success or failure.
- `details`: JSON text payload.
- `created_at`: timezone-aware timestamp (indexed).

The `AuditRepository` provides `add` (append-only) and `list_by_actor` (query by actor, most recent first) operations. Records are never updated or deleted.

### 10.2 EventRecord (Event Sourcing)

The `EventRecord` model (`event_store` table) is an append-only event store:

- `sequence`: monotonically increasing BigInteger primary key preserving global insertion order.
- `event_id`, `event_type`, `event_category`: typed event metadata (indexed).
- `correlation_id`: links related events across services (indexed).
- `payload`: the event data as text.
- `created_at`: timezone-aware timestamp (indexed).

Events are never updated or deleted. The platform can be rebuilt by replaying the event store in sequence order.

### 10.3 Security Events

The security event factories (`auth.events.security_events`) emit typed, immutable events in the `SECURITY` category:

- `AuthenticationFailed` -- emitted on failed authentication.
- `AuthorizationDenied` -- emitted on authorization denial.
- `SecretRotated` -- emitted when a secret or key is rotated.
- `SecurityViolationDetected` -- emitted on security violation.
- `KnowledgeAccessDenied` -- emitted when access to knowledge is denied.
- `ToolExecutionDenied` -- emitted when a tool execution is blocked.

All events carry a producer identifier (`security-runtime`) and are timestamped.

### 10.4 Security Analytics

The `SecurityAnalytics` service aggregates security signal counters (authentication attempts, authorization failures, permission violations, suspicious activity) in a `Counter` for operational monitoring.

---

## 11. Policy Recommendations

### 11.1 AI-Generated Policy Recommendations

The `PolicyRecommendation` model stores AI-generated access policy suggestions that are pending human review. Each recommendation carries:

- `policies_json`: the proposed policy set as JSON.
- `org_snapshot`: a point-in-time snapshot of the organization structure used for analysis.
- `status`: lifecycle state -- `pending`, `approved`, `rejected`, or `modified`.
- `reviewed_by`: the agent or human who reviewed the recommendation.
- `reviewed_at`: when the review occurred.

### 11.2 Review Workflow

1. A policy analysis task is triggered via `POST /policies/recommendations?project_id=...`. The analysis runs asynchronously in the background.
2. Results are stored with status `pending`.
3. A reviewer (typically the CTO agent) approves, rejects, or modifies the recommendation.
4. Approved recommendations are converted into active `AccessPolicy` rows.

The system enforces that only one analysis task runs per project at a time. Recommendations are never auto-applied -- they always require explicit human or governance approval.

---

## 12. Compliance Controls

### 12.1 Retention and Legal Hold

The `ComplianceEngine` implements:

- **Legal hold**: subjects under legal hold cannot be deleted or forgotten.
- **Right to be forgotten**: the `forget` method honors deletion requests unless blocked by a legal hold.
- **Retention expiry**: computed from a creation timestamp and a configurable retention window in days.

### 12.2 Database Integrity Constraints

Connector ingestion migrations enforce data integrity through:

- CHECK constraints on all state columns (enumerated valid states).
- CHECK constraints on all counter/progress columns (non-negative).
- Composite foreign keys scoped to `organization_id` preventing cross-tenant references.
- Unique constraints on provenance tuples.

---

## Source Files

Key files referenced in this document:

| Area | Path |
|------|------|
| Auth module init | `backend/ecms/auth/__init__.py` |
| JWT codec | `backend/ecms/auth/infrastructure/jwt_codec.py` |
| JWT auth service | `backend/ecms/auth/services/authentication_service.py` |
| Password hasher | `backend/ecms/auth/infrastructure/password.py` |
| API key manager | `backend/ecms/auth/infrastructure/api_keys.py` |
| Bearer extraction | `backend/ecms/auth/infrastructure/bearer.py` |
| Authorization service | `backend/ecms/auth/services/authorization_service.py` |
| Authorization domain | `backend/ecms/auth/domain/authorization.py` |
| Identity model | `backend/ecms/auth/domain/identity.py` |
| Token models | `backend/ecms/auth/domain/tokens.py` |
| Auth REST routes | `backend/ecms/api/rest/auth.py` |
| Encryption service | `backend/ecms/auth/services/encryption.py` |
| Compliance engine | `backend/ecms/auth/services/compliance.py` |
| Security analytics | `backend/ecms/auth/services/analytics.py` |
| Security events | `backend/ecms/auth/events/security_events.py` |
| Auth interfaces | `backend/ecms/auth/interfaces/service.py`, `authorization.py` |
| Access policy model | `backend/ecms/persistence/models/access_policy.py` |
| Access policy engine | `backend/ecms/agent/access_engine.py` |
| Policy REST API | `backend/ecms/api/rest/policies.py` |
| Agent model | `backend/ecms/persistence/models/agent.py` |
| Agent permissions | `backend/ecms/agent/permissions.py` |
| Governance model | `backend/ecms/persistence/models/governance_assignment.py` |
| Governance repo | `backend/ecms/persistence/repositories/governance_assignment.py` |
| Governance REST API | `backend/ecms/api/rest/governance.py` |
| Audit model | `backend/ecms/persistence/models/audit.py` |
| Audit repository | `backend/ecms/persistence/repositories/audit.py` |
| Event model | `backend/ecms/persistence/models/event.py` |
| Aggregate model | `backend/ecms/persistence/models/aggregate.py` |
| Settings | `backend/ecms/configuration/schemas/settings.py` |
| Redaction utilities | `backend/ecms/shared/security/redaction.py` |
| Git runtime | `backend/ecms/connectors/ingestion/git_runtime.py` |
| Rate limit middleware | `backend/ecms/api/middleware/rate_limit.py` |
| Request context middleware | `backend/ecms/api/middleware/context.py` |
| Observability middleware | `backend/ecms/api/middleware/observability.py` |
| App factory | `backend/ecms/api/app.py` |
| Backend Dockerfile | `docker/backend.Dockerfile` |
| Prod compose | `docker/docker-compose.prod.yml` |
| K8s backend deployment | `kubernetes/base/backend.yaml` |
