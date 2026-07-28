# AegisAI Engineering and Coding Standards

This document defines the permanent engineering and coding standards for AegisAI. These rules apply universally to every language, framework, and service within the platform. The objective is to ensure consistency, maintainability, scalability, and enterprise-grade quality across the entire codebase.

## 1. Engineering Philosophy
Code is read far more often than it is written. Optimization must target human comprehension first, and machine execution second, unless explicitly dealing with a critical bottleneck. Every line of code must defend the core principles of AegisAI: **Control, Governance, and Accountability**. 

## 2. Code Organization Principles
Code must be organized logically by domain, not merely by technical layer. Features should be self-contained where possible, exposing only explicit public interfaces to other domains.

## 3. SOLID Principles
* **Single Responsibility**: A class or module should have one, and only one, reason to change.
* **Open/Closed**: Software entities should be open for extension but closed for modification.
* **Liskov Substitution**: Subtypes must be substitutable for their base types.
* **Interface Segregation**: Clients should not be forced to depend on interfaces they do not use.
* **Dependency Inversion**: High-level modules should not depend on low-level modules; both should depend on abstractions.

## 4. Clean Architecture Principles
The core business logic (Domain) must reside at the center of the architecture, entirely independent of UI, databases, frameworks, or external APIs. External layers depend inward.

## 5. Separation of Concerns
Distinct aspects of the application (e.g., rendering, data fetching, business logic, authorization) must not be entangled. 
* *Bad*: A UI component querying the database directly.
* *Good*: A UI component calls an API, which invokes a use-case, which retrieves data via a repository.

## 6. Single Responsibility
Functions, classes, and modules must do exactly one thing. If a function name includes "And", it likely violates this rule.

## 7. Naming Conventions
Names must reveal intent. They should be clear, concise, and searchable. Avoid abbreviations and acronyms unless they are universally understood domain terms.

## 8. Folder Structure Rules
* Group by domain/feature, then by technical concern.
* Use `kebab-case` for all folder names.
* Keep structures flat where possible; avoid deeply nested hierarchies unless strictly necessary.

## 9. File Naming Rules
* Standardize on `kebab-case.ext` for files, except for classes/components where language conventions dictate `PascalCase.ext`.
* The file name must match the primary export or class name exactly.

## 10. Class Naming Rules
* Use `PascalCase`.
* Names must be nouns representing objects or concepts (e.g., `UserRepository`, `ApprovalWorkflow`).

## 11. Function Naming Rules
* Use `camelCase` (or `snake_case` in languages where standard).
* Names must be verbs or verb phrases indicating the action performed (e.g., `executeTask`, `validatePermissions`).

## 12. Variable Naming Rules
* Use `camelCase`.
* Booleans must be prefixed with `is`, `has`, `should`, or `can` (e.g., `isAuthorized`).
* Arrays or collections must be pluralized (e.g., `users`, `activePolicies`).

## 13. API Naming Rules
* RESTful endpoints must use nouns, be pluralized, and utilize standard HTTP methods.
* Paths must be `kebab-case`.
* *Example*: `GET /api/v1/organizations/{id}/users`

## 14. Database Naming Rules
* Table names: plural, `snake_case` (e.g., `audit_logs`).
* Column names: `snake_case`.
* Foreign keys must explicitly suffix `_id` (e.g., `owner_id`).

## 15. Event Naming Rules
* Events must represent something that happened in the past.
* Use past-tense verbs.
* *Example*: `UserAuthenticated`, `TaskExecutionFailed`.

## 16. Logging Standards
* Do not use `console.log` or standard print statements; use the platform's structured logging library.
* Include tracing IDs (e.g., Request ID, Correlation ID) in every log.
* **Never** log PII, credentials, or secure tokens.

## 17. Error Handling Standards
* Catch errors at the lowest possible level, wrap them with domain context, and bubble them up.
* Never swallow errors silently.
* Differentiate between expected operational errors (e.g., Validation Error) and unexpected systemic errors (e.g., Database Timeout).

## 18. Validation Standards
* Validate all inputs at the outermost boundary (API controllers, UI forms).
* Re-validate business rules (Ownership, Permissions) at the innermost execution core.
* Fail fast.

## 19. Security Standards
* Encrypt all secrets at rest.
* Require TLS for all transit.
* Sanitize all inputs to prevent injection.
* Follow the Principle of Least Privilege for all service accounts and API roles.

## 20. Testing Standards
* Code is incomplete without tests.
* Unit tests must cover business logic and edge cases.
* Integration tests must cover database queries and API boundaries.
* E2E tests must cover critical user journeys.

## 21. Documentation Standards
* Code should be self-documenting through clear naming and small functions.
* Use comments to explain *why*, not *what*.
* Maintain updated OpenAPI/Swagger specs for all APIs.

## 22. Versioning Standards
* Use Semantic Versioning (SemVer).
* External APIs must be explicitly versioned in the URL or headers (e.g., `v1`).
* Never introduce breaking changes to a stable API without a deprecation phase.

## 23. Dependency Management Rules
* Keep dependencies to an absolute minimum.
* Pin dependency versions strictly.
* Audit dependencies automatically for vulnerabilities before merging.

## 24. Configuration Rules
* Configuration must be injected via environment variables.
* Never commit secrets, keys, or passwords into source control.
* Provide clean fallback defaults for local development.

## 25. Feature Flag Rules
* Use feature flags for incomplete work or dark launches.
* Remove feature flags immediately once a feature is fully rolled out.

## 26. Code Review Rules
* Reviews must verify adherence to architecture documents, not just syntax.
* Reviewers must ensure the code does not violate Control, Governance, or Accountability.
* All PRs require at least one human approval.

## 27. Pull Request Rules
* Keep PRs small and focused on a single concern.
* The PR description must link to the architectural specification or ticket.
* All CI checks must pass before merging.

## 28. Refactoring Rules
* Leave the codebase better than you found it (The Boy Scout Rule).
* Do not mix refactoring with feature development in the same PR.

## 29. Performance Guidelines
* Avoid premature optimization, but respect big-O complexity in critical paths.
* Offload heavy processing to background workers via the Task Engine.

## 30. Scalability Guidelines
* Services must be stateless to support horizontal scaling.
* Cache read-heavy, slow-changing data (e.g., RBAC policies).

## 31. Maintainability Guidelines
* Avoid "clever" code; prefer explicit, simple logic.
* Limit function length; if a function requires scrolling to read, it is too long.

## 32. Forbidden Practices
The following practices are strictly forbidden across the entire platform:

* **Hardcoded secrets**: Passwords, API keys, and tokens must never appear in code.
* **Hardcoded permissions**: Do not use `if (user == "admin")`; query the RBAC engine.
* **Business logic inside controllers**: Controllers only route data; logic belongs in services/use-cases.
* **Circular dependencies**: Module A cannot depend on Module B if Module B depends on Module A.
* **Duplicate code**: Extract reusable logic into shared packages.
* **Magic strings/numbers**: Extract them into named constants or enums.
* **Direct database access from UI**: UI must strictly communicate through the API layer.
* **Direct AI provider access outside Runtime**: Only the Runtime module may communicate with OpenAI, Anthropic, etc.
* **Bypassing Guardian**: No execution flow may circumvent the Guardian validation checkpoint.
* **Skipping Audit**: State mutations must always generate an audit trail.
* **Ignoring Ownership validation**: You must never act on an asset without validating ownership.
* **Ignoring Approval flow**: You must never execute sensitive logic without fulfilling approval requirements.

---

## Non-Negotiable Engineering Rules
Every contributor and AI assistant must permanently follow these rules:

1. **Architecture First**: No implementation may occur without an approved architectural document in `.aegis/`.
2. **Governance is Absolute**: No code shall be merged that weakens the Control, Governance, or Accountability of the platform.
3. **Guardian is Supreme**: Bypassing Guardian for execution or authorization is a catastrophic violation and is strictly prohibited.
4. **Audit Everything**: If it mutates state or makes a decision, it must be durably logged to the Audit ledger.
5. **No AI Autonomy**: No AI component may autonomously modify security, alter governance, or approve its own actions.
