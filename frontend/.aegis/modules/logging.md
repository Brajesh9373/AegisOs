# AegisAI Logging Architecture Specification

This document defines the definitive, permanent Logging Architecture for AegisAI. It establishes the rules, formatting, and lifecycle of application telemetry, separating operational diagnostics from the immutable Audit Ledger.

## 1. Logging Philosophy
Logs are the pulse of the system, designed for engineers to diagnose, trace, and debug. The Audit Ledger is designed for lawyers to prove accountability. Logs are ephemeral, high-volume, and deeply technical. An Enterprise AI OS must log heavily to trace complex, non-deterministic LLM behaviors without ever leaking sensitive tenant data or secrets into standard output.

## 2. Objectives
The Logging Architecture must:
* Provide a standardized, structured (JSON) logging format across all microservices and workers.
* Ensure every log entry is intrinsically tied to a specific trace, tenant, and user context.
* Prevent the leakage of API keys, PII, and raw prompt content into diagnostic streams.
* Facilitate high-speed ingestion into centralized logging platforms (e.g., Datadog, ELK, Splunk).

## 3. Logging Architecture
AegisAI utilizes a central logging library injected into every process. Logs are written asynchronously to standard output (`stdout`) in JSON format. The container orchestration layer (e.g., Kubernetes FluentBit) scrapes `stdout`, applies global redaction rules, and forwards the stream to a central Log Aggregator.

## 4. Structured Logging
Plain text logging (`console.log("Task started")`) is strictly forbidden. All logs must be structured JSON, ensuring that fields like `tenant_id`, `trace_id`, and `latency_ms` are queryable integers or strings, not regex-parsed text.

## 5. Log Categories
Logs are categorized to facilitate routing and retention.
* `sys`: Infrastructure and boot sequence.
* `app`: Standard application logic.
* `sec`: Authentication and Guardian block events.
* `ai`: LLM orchestration and token metrics.

## 6. Runtime Logs
High-volume telemetry from the Task Engine. Includes queue latency, worker saturation, and task state transitions.

## 7. Guardian Logs
Diagnostic logs related to policy evaluation. While a Guardian block generates an Audit Ledger entry, the *reasoning* and latency of the policy evaluation are written to the Runtime Logs.

## 8. Agent Logs
Trace data for AI execution. Includes prompt assembly times, tool selection logic, and API timeout events.

## 9. API Logs
Standard HTTP access logs. Includes Request Method, Path, Status Code, IP Address, and Latency.

## 10. Security Logs
Failed login attempts, rate-limit triggers, and abnormal payload sizes. (These also trigger formal Audit Events, but the raw network telemetry belongs in the log stream).

## 11. Audit Integration
Logs never replace Audit. If a log indicates a system failure, it is diagnostic. If a log indicates an administrator changed a setting, that is a governance event and must go to the immutable Audit Ledger, not just `stdout`.

## 12. Correlation IDs
Every incoming HTTP request or Event Bus trigger is assigned a unique `correlation_id`. This ID is passed to every downstream service, worker, and database query, ensuring a single logical action can be traced across the entire distributed system.

## 13. Trace IDs
Specific to OpenTelemetry distributed tracing. Used for visualizing the waterfall latency of microservice interactions.

## 14. Log Levels
* `TRACE`: Extreme detail (e.g., raw HTTP headers). Disabled in production.
* `DEBUG`: Diagnostic info (e.g., database query strings).
* `INFO`: Standard lifecycle events (e.g., Task Started).
* `WARN`: Handled errors, retries, or degraded performance.
* `ERROR`: Unhandled exceptions, dropped events, or system crashes.
* `FATAL`: The process cannot continue and is exiting.

## 15. Log Context
Every log entry must append the current execution context automatically: `timestamp`, `service_name`, `version`, `tenant_id`, `user_id`, `correlation_id`.

## 16. Log Retention
Diagnostic logs are voluminous and expensive. They follow a strict TTL (e.g., 14 days in hot storage, 30 days in cold storage) before deletion.

## 17. Log Rotation
If writing to local disk (in edge deployments), logs must rotate daily or at 100MB to prevent disk exhaustion.

## 18. Log Export
The Log Aggregator supports exporting specific log queries to CSV/JSON for engineering post-mortems.

## 19. Log Search
Engineers use the Log Aggregator's query language to filter by structured keys (e.g., `level:ERROR AND tenant_id:org_123`).

## 20. Log Monitoring
The Log Aggregator continuously monitors the stream. If `level:ERROR` spikes by 200% within 5 minutes, an automated page is sent to the on-call engineer.

## 21. Log Privacy
Logs are organization-aware but are primarily viewed by platform engineers, not tenant users. Therefore, logs must never contain tenant-specific PII or PHI.

## 22. Log Redaction
The logging library implements an active Redaction Engine. Any key matching specific patterns (`password`, `api_key`, `authorization`, `credit_card`) is overwritten with `[REDACTED]` before serialization.

## 23. Performance Logging
Specific logs emitted solely to calculate metrics (e.g., `event:db_query, latency_ms:45`).

## 24. Error Logging
When `level:ERROR` is triggered, the logger automatically captures and appends the full stack trace, the raw exception message, and the immediate context variables.

## 25. Future Expansion
Integration with AI Log Analysis, where an internal meta-Agent continuously reads the `WARN` and `ERROR` streams to automatically draft Root Cause Analysis (RCA) documents.

## 26. Permanent Constraints
* Logs never replace the immutable Audit Ledger.
* All logs must be structured JSON.
* Logs must explicitly scrub and redact secrets.
* Logs must support distributed tracing via `correlation_id`.
* Logs must be organization-aware (tagged with `tenant_id`).

---

## Never Do

* **Never** log passwords, OAuth tokens, session cookies, or raw database connection strings.
* **Never** log the raw text of a User Prompt or an LLM Response in production, as this bypasses PII and Privacy constraints.
* **Never** use blocking, synchronous I/O to write logs; logging must never slow down the primary execution thread.
* **Never** catch an exception, log it as `INFO`, and proceed; exceptions are `ERROR`s or `WARN`ings.

---

## Logging Constitution
The permanent Logging principles of AegisAI:
1. **The Principle of Structure**: A log is data, not a novel. It is meant to be queried by machines, not just read by humans.
2. **The Principle of Traceability**: A system without correlation IDs is a system that cannot be debugged. Every action must leave a connected trail of breadcrumbs.
3. **The Principle of Diagnostic Segregation**: Logs are for fixing the engine; Audit is for flying the plane. They are distinct architectures with distinct rules.
