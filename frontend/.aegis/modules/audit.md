# AegisAI Audit Architecture Specification

This document defines the definitive, permanent Audit Architecture for AegisAI. It establishes the rules, structure, and governance required to maintain a cryptographically verifiable, immutable ledger of every significant action within the platform.

## 1. Audit Philosophy
In an Enterprise AI OS, accountability is impossible without an unbroken chain of evidence. The Audit Ledger is the absolute, unquestionable historical truth of the platform. If an action is not recorded in the Audit log, it did not happen. If an AI makes a mistake, the Audit log must prove exactly why, how, and under whose authority it occurred.

## 2. Objectives
The Audit Architecture must:
* Provide a 100% immutable, WORM (Write Once, Read Many) log of all system mutations.
* Ensure every entry is irrefutably tied to a Human Owner or System Actor.
* Guarantee that no user, including Tenant Administrators, can alter or delete an audit record.
* Facilitate rapid, granular eDiscovery for legal and compliance teams.

## 3. Audit Architecture
The Audit Engine acts as a specialized, high-privilege consumer of the internal Event Bus. It intercepts all mutation events (e.g., API requests, Task completions, Guardian checks) and persists them directly into a specialized, append-only datastore.

## 4. Immutable Audit Logs
Every record written to the Audit datastore is cryptographically hashed. The hash of each new record includes the hash of the previous record, creating a tamper-evident blockchain-like structure within the database.

## 5. Audit Ownership
Audit logs belong to the Organization. However, access to view them is strictly governed by RBAC (e.g., only Compliance Officers or Tenant Admins can view the global ledger).

## 6. Audit Lifecycle
Event Fired → Intercepted by Audit Engine → Hashed & Persisted → Indexed for Search → Retained per Policy → Exported (if requested).

## 7. Audit Categories
Audit logs are rigidly structured by domain to allow precise querying.

## 8. Security Audit
Logs related to policy changes, Guardian interceptions, and detected anomalies.

## 9. Runtime Audit
Logs capturing the exact LLM prompt sent, the LLM response received, and the tool payload requested.

## 10. Guardian Audit
Logs detailing *why* Guardian approved or denied a specific action, including the exact policy ID evaluated.

## 11. Agent Audit
Logs tracking the lifecycle of an Agent (Creation, Modification, Archival, Assignment).

## 12. Skill Audit
Logs recording every invocation of a Skill, including the input variables and the final execution output.

## 13. Memory Audit
Logs capturing manual or automated alterations to an Agent's working memory.

## 14. Knowledge Audit
Logs tracking the upload, modification, certification, or deletion of authoritative Knowledge documents.

## 15. Task Audit
Logs tracking the state transitions of a Task (Queued → Running → Completed/Failed).

## 16. Approval Audit
Logs capturing the exact cryptographic signature of a human approving a high-risk Task.

## 17. License Audit
Logs tracking license activation, renewal, expiration, and threshold breaches.

## 18. User Audit
Logs tracking user provisioning, role changes, and account suspensions.

## 19. Organization Audit
Logs tracking global tenant settings changes (e.g., changing the SSO provider).

## 20. API Audit
Logs tracking all `POST`, `PUT`, `PATCH`, and `DELETE` requests at the API Gateway layer, regardless of success or failure.

## 21. Configuration Audit
Logs tracking modifications to system environment variables or application configuration files.

## 22. Authentication Audit
Logs tracking successful logins, failed logins, MFA challenges, and token revocations.

## 23. Authorization Audit
Logs tracking RBAC checks, particularly when a user is denied access to a requested resource.

## 24. Change Tracking
Every mutation audit log must include a clear `before` and `after` state (JSON diff) of the mutated entity.

## 25. History Tracking
The Audit UI allows an administrator to view the complete chronological history of any specific entity (e.g., "Show me everything that has ever happened to Task #1234").

## 26. Version Tracking
When an entity (like a Knowledge Doc or Agent Prompt) is updated, the Audit log references the explicit version numbers (e.g., `v2 -> v3`).

## 27. Evidence Collection
For highly sensitive actions, the Audit log may capture secondary evidence, such as the IP address, User-Agent, and geographic location of the human actor.

## 28. Correlation IDs
Every audit log must contain the `correlation_id` initiated by the origin API request. This allows analysts to group all logs associated with a single user action.

## 29. Event Correlation
The Audit UI must be able to stitch together API Audits, Guardian Audits, and Runtime Audits into a single unified timeline using the `correlation_id`.

## 30. Search
The Audit datastore must support high-performance, full-text search across all log payloads.

## 31. Filtering
The UI must allow complex Boolean filtering (e.g., `Actor = "John Doe" AND Category = "Skill Audit" AND Status = "Failed"`).

## 32. Retention
Audit logs must be retained according to strict organizational policies (e.g., 7 years for financial institutions). The platform must enforce minimum retention periods that cannot be bypassed.

## 33. Export
Authorized administrators can export filtered Audit logs to standard formats (CSV, JSON) or securely forward them to external SIEM systems (e.g., Splunk, QRadar).

## 34. Compliance
The architecture is designed to instantly satisfy eDiscovery requests and pass SOC2/ISO27001 evidence requirements out-of-the-box.

## 35. Monitoring
The platform actively monitors the health of the Audit datastore. If the Audit Engine fails to write a log, the core platform must instantly degrade to a "fail-closed" read-only state until auditing is restored.

## 36. Future Expansion
The architecture supports the future addition of automated compliance reporting (e.g., generating a monthly PDF proving no unauthorized DB drops occurred).

## 37. Permanent Constraints
* Audit logs are strictly immutable.
* Audit logs are append-only.
* Nothing bypasses Audit.
* Every action has an actor.
* Every action has a timestamp.
* Every action has traceability.
* Audit records are never silently modified.

---

## Enterprise Examples

**Legal eDiscovery Example:**
An employee deletes a critical financial Knowledge document before leaving the company. Legal requests an audit. The Compliance Officer filters the Audit UI by `Resource: Financial_SOP.pdf` and `Category: Knowledge Audit`. The ledger shows the exact timestamp, the employee's ID, the IP address, and the API request that triggered the deletion.

**AI Hallucination Debugging:**
An Agent executes a Jira ticket creation incorrectly. The developer searches the Task ID in the Audit UI. Using the `correlation_id`, they view the `Runtime Audit` to see the exact prompt the LLM received, the `Knowledge Audit` to see what context was injected, and the `Guardian Audit` to verify why the execution was allowed.

---

## Never Do

* **Never** allow any user, regardless of their administrative privileges, to execute an `UPDATE` or `DELETE` statement against the Audit datastore.
* **Never** log plaintext passwords, authentication tokens, or raw PII (like credit card numbers) into the Audit log. Mask them before persistence.
* **Never** allow an API request to succeed if the asynchronous Audit event dispatch fails.
* **Never** truncate the Audit log to save disk space without first cryptographically archiving it to cold storage.
* **Never** design the Audit schema without a strict `correlation_id`; disjointed logs are useless during a crisis.

---

## Audit Constitution
The permanent Audit principles of AegisAI:
1. **The Principle of Absolute Memory**: The platform never forgets. Every mutation, every decision, and every failure is permanently etched into the ledger.
2. **The Principle of Unimpeachable Truth**: The ledger cannot be altered. It is the final arbiter of truth in any dispute between human intent and AI execution.
3. **The Principle of Shared Accountability**: By recording exactly what the AI did and who authorized it, the Audit ledger ensures that human owners remain fully responsible for the actions of their digital delegates.
