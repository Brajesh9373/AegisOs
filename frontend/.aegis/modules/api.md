# AegisAI API Architecture Specification

This document defines the definitive, permanent API Architecture for AegisAI. It establishes the rules, design standards, integration points, and governance model for all programmatic access to the platform.

## 1. API Philosophy
The API is the universal contract of AegisAI. It is the sole mechanism for interacting with the platform's core capabilities. Every UI element, CLI tool, external integration, and internal microservice must consume the exact same API. The API is designed for absolute predictability, rigorous governance, and enterprise scalability.

## 2. Objectives
The API Architecture must:
* Provide a stable, versioned, and predictable RESTful interface.
* Enforce 100% compliance with Guardian, RBAC, and Audit policies.
* Ensure secure, scalable, multi-tenant isolation.
* Deliver consistent response and error structures across all endpoints.

## 3. API Architecture
The API layer acts as a strictly defined gateway. It is a stateless orchestration layer that authenticates the caller, resolves the organizational context, routes the request to the business logic domain (e.g., Task Engine, Memory), and returns a standardized response envelope.

## 4. API Versioning Strategy
APIs are versioned explicitly in the URI (e.g., `/api/v1/`). Major versions indicate breaking changes. Minor changes (additions) are continuously rolled into the current major version. Legacy versions are maintained according to a strict deprecation policy.

## 5. REST Design Principles
The API strictly adheres to RESTful principles. State transitions are managed through standard HTTP methods acting upon clearly defined nouns (resources). 

## 6. Resource Naming Standards
* Resources must be **nouns**, never verbs.
* Resources must always be **pluralized**.
* Words must be separated by hyphens (`kebab-case`).
* Example: `/api/v1/task-executions`

## 7. URI Standards
URIs must represent the hierarchical relationship of resources.
* Root resource: `/{version}/{resource}`
* Specific resource: `/{version}/{resource}/{id}`
* Nested resource: `/{version}/{parent-resource}/{parent-id}/{child-resource}`
* Avoid nesting beyond two levels; extract to a top-level resource with query filters if necessary.

## 8. HTTP Method Standards
* `GET`: Retrieve a resource or list of resources. Always idempotent.
* `POST`: Create a new resource or trigger an action (if a verb is unavoidable, it must be a sub-resource, e.g., `/api/v1/tasks/{id}/approve`).
* `PUT`: Completely replace an existing resource. Idempotent.
* `PATCH`: Partially update a resource. 
* `DELETE`: Soft-delete or archive a resource.

## 9. Request Standards
All request bodies must be `application/json`. Multi-part form data is strictly reserved for binary file uploads.

## 10. Response Standards
All responses must return `application/json`. Responses must follow a standardized envelope structure separating `data` from `meta`.

**Standard Response Envelope:**
```json
{
  "data": { ... or [ ... ] },
  "meta": {
    "request_id": "req-12345",
    "timestamp": "2026-06-30T12:00:00Z"
  }
}
```

## 11. Error Response Standards
Errors must never leak stack traces or internal implementation details. They must provide actionable context to the consumer.

**Standard Error Envelope:**
```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The provided email format is invalid.",
    "details": [
      { "field": "email", "issue": "Must be a valid organizational domain." }
    ]
  },
  "meta": {
    "request_id": "req-12345",
    "timestamp": "2026-06-30T12:00:00Z"
  }
}
```

## 12. Authentication Architecture
The API supports stateless authentication via JWTs (Bearer tokens). The token cryptographically asserts the User ID, active Organization ID, and session expiration.

## 13. Authorization Integration
Authentication proves *who* the caller is; Authorization (RBAC) proves *what* they can do. The API controllers pass the resolved identity to the domain layer, which queries the RBAC engine before any read or write operation.

## 14. Guardian Integration
For all execution and mutation endpoints, the API acts as a passthrough to Guardian. The API controller formats the intent and submits it to Guardian. If Guardian rejects the request, the API instantly returns a `403 Forbidden` with a standardized policy violation code.

## 15. Runtime Integration
The API endpoints for interacting with Agents (e.g., sending a chat message) are asynchronous. The API acknowledges the request (`202 Accepted`) and hands the payload to the Task Engine, which orchestrates the Runtime execution.

## 16. RBAC Integration
Every endpoint must explicitly define the required RBAC permission (e.g., `Read:Agent`, `Create:Task`). The framework must enforce this permission declaration at the routing layer before executing controller logic.

## 17. Organization Context
In a multi-tenant setup, the Organization ID is implicitly derived from the authenticated token or the explicitly requested workspace domain (e.g., `https://{workspace-domain}/api/v1/...`). It must never be accepted blindly from a client payload (e.g., never trust `{"org_id": "123"}` in a POST body).

## 18. Workspace Context
Similar to Organization Context, Workspace boundaries are cryptographically enforced based on the authentication token and the targeted URI.

## 19. Multi-Tenant API Strategy
All database queries initiated by the API must implicitly include the Organization ID derived from the authenticated context to prevent cross-tenant data leakage.

## 20. Pagination Standards
All list endpoints must be paginated using cursor-based pagination (for high performance/deep scaling) or offset-based pagination (for simple lists). 

**Pagination Metadata Example:**
```json
"meta": {
  "pagination": {
    "next_cursor": "cGFnZTI=",
    "has_more": true,
    "total_count": 142
  }
}
```

## 21. Filtering Standards
Filters are passed as query parameters using standard naming (e.g., `?status=active&department_id=hr-123`). Complex filters should utilize structured query syntax if required.

## 22. Sorting Standards
Sorting is passed via a `sort` query parameter. Prefix with `-` for descending order (e.g., `?sort=-created_at,name`).

## 23. Search Standards
Text-based search uses a `q` parameter (e.g., `?q=security`). The API delegates this to the backend search engine.

## 24. Bulk Operations
Bulk operations must accept arrays of payloads and return a structured response detailing successes and individual failures (e.g., `207 Multi-Status`).

## 25. Long Running Operations
Endpoints that trigger long-running actions (e.g., training an agent) must return a `202 Accepted` with a `Location` header pointing to a Task resource where the client can poll for status.

## 26. Async Operations
For async tasks, the API embraces event-driven design, encouraging clients to rely on webhooks or WebSocket events rather than aggressive polling.

## 27. File Upload Standards
Uploads use `multipart/form-data`. The API validates mime types, file sizes, and scans for malware before passing the stream to the storage layer.

## 28. File Download Standards
Downloads return standard HTTP streams with appropriate `Content-Disposition` and `Content-Type` headers. Temporary signed URLs are preferred for massive assets.

## 29. Streaming Standards
Real-time LLM responses use Server-Sent Events (SSE) or WebSockets to stream tokens to the client efficiently.

## 30. Validation Standards
All inputs (URL parameters, query strings, bodies) must be rigorously validated against a strict schema before the controller executes.

## 31. Error Handling
Controllers never handle raw exceptions. A global error handler catches all exceptions, logs the stack trace internally, and maps the exception to a Standard Error Envelope.

## 32. Standard Error Codes
* `400 Bad Request`: Validation failure.
* `401 Unauthorized`: Invalid or missing token.
* `403 Forbidden`: RBAC or Guardian denial.
* `404 Not Found`: Resource does not exist (or the user lacks permission to know it exists).
* `409 Conflict`: Resource state conflict (e.g., duplicate unique key).
* `429 Too Many Requests`: Rate limit exceeded.
* `500 Internal Server Error`: Unhandled system failure.

## 33. API Security
* Always use HTTPS (`TLS 1.2+`).
* Enforce strict CORS policies.
* Sanitize all inputs against SQLi and XSS.

## 34. Rate Limiting Strategy
APIs are rate-limited by User IP and Tenant ID to prevent noisy-neighbor degradation. `429 Too Many Requests` includes `Retry-After` headers.

## 35. Idempotency Strategy
All `POST` operations that mutate critical state (e.g., financial transactions, agent creation) must accept an `Idempotency-Key` header to safely handle client retries.

## 36. Request Correlation
The client may provide a `X-Correlation-ID`. The API must propagate this ID through all internal microservices and include it in the response and audit logs.

## 37. Audit Integration
The API framework automatically intercepts all mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`) and fires an async event to the Audit module detailing the exact change, who made it, and the request ID.

## 38. Monitoring Integration
Every endpoint automatically emits metrics for latency (p95, p99), status codes, and payload size.

## 39. Notification Integration
APIs do not send notifications directly. They emit domain events (e.g., `TaskCompleted`), which the Notification Engine consumes.

## 40. Event Integration
The API publishes state changes to the internal Event Bus, allowing decoupled modules to react instantly without synchronous dependencies.

## 41. API Documentation Standards
All APIs must be documented using the OpenAPI Specification (OAS 3.0+). The specification serves as the source of truth for SDK generation.

## 42. API Deprecation Strategy
Deprecated endpoints must include a `Deprecation` header and sunset date. They must remain active for a minimum of 6 months.

## 43. API Compatibility Strategy
APIs evolve without breaking clients by strictly adding fields, never removing or renaming them. If a breaking change is required, a new major version (e.g., `v2`) is deployed.

## 44. API Lifecycle
Design → Review against Architecture → OpenAPI Spec Generation → Implementation → Security Audit → Publish.

## 45. Future Expansion
The API architecture is designed to support GraphQL for specific read-heavy client UI optimization, provided the GraphQL layer strictly maps to the exact same underlying RBAC/Guardian resolvers as the REST API.

## 46. Permanent Constraints
* APIs never bypass Guardian.
* APIs never bypass RBAC.
* APIs never bypass Audit.
* APIs never expose internal implementation (e.g., database columns, stack traces).
* APIs never leak internal errors.
* APIs are always versioned.
* APIs are backward compatible whenever possible.
* APIs are fully documented.
* APIs are fully auditable.
* APIs are organization aware.
* APIs are workspace aware.
* APIs are secure by default.

---

## Never Do

* **Never** use verbs in REST endpoint URLs (e.g., use `POST /api/v1/tasks`, not `POST /api/v1/createTask`).
* **Never** hardcode base URLs or domains in client-facing documentation or code; use placeholders like `https://{api-host}/api/v1/`.
* **Never** trust the client-provided `Organization-ID` or `User-ID` in a payload; always extract identity from the cryptographic token.
* **Never** return a `200 OK` for a failed operation with an error object inside the body. Use the correct HTTP status code.
* **Never** return partial data that the user is not authorized to see; filter strictly at the database query level.
* **Never** process long-running AI generation synchronously in an HTTP request.
* **Never** allow external API requests to bypass standard Rate Limiting boundaries.

---

## API Constitution
The permanent API principles of AegisAI:
1. **The API is the Platform**: There are no backdoors, no CLI bypasses, and no UI shortcuts. If the platform can do it, it is exposed via the versioned API.
2. **Absolute Defense**: The API assumes every request is hostile. It validates identity, context, format, and policy before a single byte of business logic is executed.
3. **Impeccable Predictability**: Clients must never guess how to parse an error, paginate a list, or authenticate. The contract is rigid, consistent, and meticulously documented.
