# AegisAI API Contract Specification

This document defines the REST API Contract for AegisAI. It establishes the precise inputs, outputs, validation rules, and security contexts for the platform's core endpoints.

## Global API Rules
*   **Protocol:** HTTPS only. All payloads are `application/json`.
*   **Authentication:** Requires a valid `Bearer` token (JWT) in the `Authorization` header.
*   **Authorization:** The API Gateway validates the JWT against RBAC roles before reaching the endpoint.
*   **Tenant Scoping:** All requests are implicitly scoped to the User's active `organization_id` derived from the token. Cross-tenant access is impossible.
*   **Versioning:** Endpoints are prefixed with `/api/v1/`.
*   **Pagination:** List endpoints return `data`, `meta.current_page`, `meta.total_pages`, `meta.total_items`.

---

## 1. Identity & Auth Module

### `POST /api/v1/auth/login`
*   **Purpose:** Authenticate a user and return a session token.
*   **Authentication:** None (Public).
*   **Authorization:** None.
*   **Request:** `{"email": "user@acme.com", "password": "...", "mfa_token": "123456"}`
*   **Response (200):** `{"token": "jwt...", "refresh_token": "...", "expires_in": 3600}`
*   **Validation:** Rate limited (max 5 attempts/minute).
*   **Error Codes:** 401 Unauthorized, 403 Forbidden (Locked), 429 Too Many Requests.
*   **Events Generated:** `UserLoggedIn`, `UserLoginFailed`.
*   **Audit Requirements:** Full audit on success and failure.

### `POST /api/v1/auth/logout`
*   **Purpose:** Invalidate the current session token.
*   **Authentication:** Bearer Token.
*   **Authorization:** Any authenticated user.
*   **Request:** `{}`
*   **Response (200):** `{"message": "Logged out successfully"}`
*   **Events Generated:** `UserLoggedOut`.
*   **Audit Requirements:** Full audit.

---

## 2. Workspace Module

### `POST /api/v1/workspaces`
*   **Purpose:** Create a new Workspace boundary.
*   **Authentication:** Bearer Token.
*   **Authorization:** `org:workspace:create`.
*   **Request:** `{"name": "Project Alpha", "description": "...", "department_id": "uuid"}`
*   **Response (201):** `{"id": "uuid", "name": "Project Alpha", "created_at": "..."}`
*   **Validation:** `name` is required, unique within Org, max 100 chars.
*   **Error Codes:** 400 Bad Request, 403 Forbidden.
*   **Events Generated:** `WorkspaceCreated`.
*   **Audit Requirements:** Full audit.

### `GET /api/v1/workspaces/{workspace_id}`
*   **Purpose:** Retrieve Workspace details.
*   **Authentication:** Bearer Token.
*   **Authorization:** `workspace:read` (must be member or admin).
*   **Response (200):** `{"id": "uuid", "name": "...", "stats": {"active_agents": 3}}`
*   **Error Codes:** 403 Forbidden, 404 Not Found.
*   **Audit Requirements:** None (Read-only).

---

## 3. Agent Module

### `POST /api/v1/workspaces/{workspace_id}/agents`
*   **Purpose:** Create a new AI Persona.
*   **Authentication:** Bearer Token.
*   **Authorization:** `workspace:agent:create`.
*   **Request:** `{"name": "SupportBot", "system_prompt": "You are a...", "model_id": "gpt-4o"}`
*   **Response (201):** `{"id": "uuid", "active_version_id": "uuid", "status": "draft"}`
*   **Validation:** `system_prompt` must pass baseline security checks.
*   **Error Codes:** 400 Bad Request.
*   **Events Generated:** `AgentCreated`.
*   **Audit Requirements:** Full audit.

### `PUT /api/v1/agents/{agent_id}/version`
*   **Purpose:** Publish a new immutable version of an Agent's configuration.
*   **Authentication:** Bearer Token.
*   **Authorization:** `workspace:agent:update`.
*   **Request:** `{"system_prompt": "Updated prompt...", "allowed_tools": ["jira_create"]}`
*   **Response (200):** `{"version_id": "uuid_v2", "promoted_at": "..."}`
*   **Events Generated:** `AgentVersionPublished`.
*   **Audit Requirements:** Strict audit (Core behavioral change).

---

## 4. Task Engine Module

### `POST /api/v1/agents/{agent_id}/tasks`
*   **Purpose:** Dispatch a new job to an Agent.
*   **Authentication:** Bearer Token.
*   **Authorization:** `agent:task:execute`.
*   **Request:** `{"prompt": "Summarize the Q3 report", "attachments": ["doc_uuid"]}`
*   **Response (202 Accepted):** `{"task_id": "uuid", "status": "queued"}` (Async execution).
*   **Validation:** Prompt length within quota. Attachments must exist in Workspace.
*   **Error Codes:** 402 Payment Required (Quota Exceeded), 403 Forbidden.
*   **Events Generated:** `TaskQueued`.
*   **Audit Requirements:** Full audit.

### `GET /api/v1/tasks/{task_id}`
*   **Purpose:** Poll the status of a running task.
*   **Authentication:** Bearer Token.
*   **Authorization:** `task:read` (Must own task or be Admin).
*   **Response (200):** `{"status": "running", "progress": 45, "current_step": "Searching Knowledge Base"}`
*   **Audit Requirements:** None.

### `POST /api/v1/tasks/{task_id}/cancel`
*   **Purpose:** Force-kill a running task.
*   **Authentication:** Bearer Token.
*   **Authorization:** `task:cancel`.
*   **Response (200):** `{"status": "cancelled"}`
*   **Events Generated:** `TaskCancelled`.
*   **Audit Requirements:** Full audit.

---

## 5. Knowledge (RAG) Module

### `POST /api/v1/workspaces/{workspace_id}/knowledge`
*   **Purpose:** Upload a document for vector embedding.
*   **Authentication:** Bearer Token.
*   **Authorization:** `workspace:knowledge:create`.
*   **Request:** `multipart/form-data` containing File and `{"title": "Q3 Report"}`
*   **Response (202 Accepted):** `{"document_id": "uuid", "status": "processing"}`
*   **Validation:** File type must be allowed (PDF, TXT, DOCX), max size 50MB.
*   **Error Codes:** 415 Unsupported Media Type, 413 Payload Too Large.
*   **Events Generated:** `KnowledgeIngestionStarted`.
*   **Audit Requirements:** Full audit (Data boundary change).

### `POST /api/v1/knowledge/search`
*   **Purpose:** Perform a raw semantic search against the Vector DB (used by UI).
*   **Authentication:** Bearer Token.
*   **Authorization:** `workspace:knowledge:read`.
*   **Request:** `{"query": "revenue metrics", "workspace_id": "uuid", "top_k": 5}`
*   **Response (200):** `{"results": [{"chunk": "...", "score": 0.92, "document_id": "uuid"}]}`
*   **Events Generated:** `KnowledgeQueried`.
*   **Audit Requirements:** Query string audited for compliance.

---

## 6. Approvals Module

### `GET /api/v1/approvals/pending`
*   **Purpose:** List workflows currently suspended waiting for the user's approval.
*   **Authentication:** Bearer Token.
*   **Authorization:** Authenticated User.
*   **Response (200):** `{"data": [{"approval_id": "uuid", "task_id": "uuid", "reason": "Requires manager override"}]}`

### `POST /api/v1/approvals/{approval_id}/resolve`
*   **Purpose:** Approve or Reject a suspended workflow.
*   **Authentication:** Bearer Token.
*   **Authorization:** User must be the designated Approver.
*   **Request:** `{"action": "APPROVE", "comment": "Looks good"}`
*   **Response (200):** `{"status": "resolved", "workflow_resumed": true}`
*   **Events Generated:** `ApprovalResolved`, `WorkflowResumed`.
*   **Audit Requirements:** Strict audit (Human chain of custody).

---

## 7. Guardian Module

### `POST /api/v1/policies`
*   **Purpose:** Create a new security or governance rule.
*   **Authentication:** Bearer Token.
*   **Authorization:** `org:policy:manage`.
*   **Request:** `{"name": "Block PII", "type": "redaction", "scope": {"department_id": "uuid"}}`
*   **Response (201):** `{"id": "uuid", "status": "active"}`
*   **Events Generated:** `PolicyCreated`.
*   **Audit Requirements:** Strict audit (Security posture change).

### `POST /api/v1/guardian/dry-run`
*   **Purpose:** Test a payload against active policies without executing it.
*   **Authentication:** Bearer Token.
*   **Authorization:** `org:policy:read`.
*   **Request:** `{"payload": "Tell me John Doe's SSN", "context_id": "workspace_uuid"}`
*   **Response (200):** `{"action": "BLOCK", "violated_policies": ["Block PII"]}`
*   **Events Generated:** None.
*   **Audit Requirements:** None.

---

## 8. Audit Module

### `GET /api/v1/audit/logs`
*   **Purpose:** Retrieve the immutable ledger.
*   **Authentication:** Bearer Token.
*   **Authorization:** `org:audit:read` (Auditor Role).
*   **Request Params:** `?start_date=...&end_date=...&user_id=...&action=AgentCreated`
*   **Response (200):** `{"data": [{"timestamp": "...", "actor": "uuid", "action": "AgentCreated", "diff": {...}}]}`
*   **Events Generated:** `AuditLogViewed`.
*   **Audit Requirements:** The act of reading the audit log is itself audited.
