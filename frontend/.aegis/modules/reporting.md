# AegisAI Reporting Architecture Specification

This document defines the definitive, permanent Reporting Architecture for AegisAI. It establishes the rules, generation mechanisms, access controls, and export standards for extracting structured insights from the platform's operational and audit datasets.

## 1. Reporting Philosophy
In an Enterprise AI OS, data without synthesis is a liability. Reporting is the mechanism by which raw audit logs and telemetry are transformed into boardroom-ready compliance evidence and operational intelligence. A report must be a pristine, mathematically verifiable reflection of the underlying data, scoped perfectly to the viewer's authority.

## 2. Objectives
The Reporting Architecture must:
* Provide standardized, reproducible extractions of platform data.
* Enforce strict RBAC filtering so reports never leak unauthorized data.
* Support asynchronous generation for massive datasets without degrading API performance.
* Deliver reports in industry-standard formats for external analysis and archiving.

## 3. Report Architecture
The Reporting Engine operates as a dedicated asynchronous worker pool. When a user requests a report, the API validates their RBAC permissions and places a job in the Reporting Queue. The worker executes the necessary OLAP queries, formats the document, saves the artifact to secure Object Storage, and notifies the user via the Notification Engine.

## 4. Report Categories
Reports are classified by intent and target audience to standardize schemas and expected outputs.

## 5. Operational Reports
Focus on velocity and throughput (e.g., "Tasks Completed by Department", "Average Task Execution Time").

## 6. Executive Reports
High-level aggregations (e.g., "Monthly Organization AI ROI", "Global Threat Interception Summary").

## 7. Security Reports
Focus on anomalies and policy enforcement (e.g., "Failed Authentication Attempts", "Guardian Blocked Actions by Severity").

## 8. Audit Reports
Strict, immutable ledgers extracted for compliance (e.g., "SOC2 Access Control Log", "Complete Change History for Agent XYZ").

## 9. Runtime Reports
Detailed metrics on LLM behavior (e.g., "Token Consumption by Model", "Average Context Assembly Latency").

## 10. License Reports
Entitlement tracking (e.g., "Active Seat Utilization", "Approaching Storage Limits").

## 11. Agent Reports
Performance of specific AI personas (e.g., "SupportBot Resolution Rate", "Agent Error Frequency").

## 12. Skill Reports
Utilization of integrations (e.g., "Most Frequently Invoked Skills", "Skill Failure Rates").

## 13. Knowledge Reports
Governance of the document library (e.g., "Expiring Certifications", "Most Referenced Knowledge Assets").

## 14. Memory Reports
Analysis of agent context (e.g., "Memory Growth per Agent", "Archived Memory Volume").

## 15. Cost Reports
FinOps reporting mapping token usage and infrastructure costs back to specific Workspaces and Departments.

## 16. Scheduled Reports
The Engine supports `cron`-based scheduling. Reports can be generated automatically (e.g., Daily, Weekly, Monthly) and distributed to specific User Groups or external email addresses.

## 17. On Demand Reports
Ad-hoc reports generated instantly via the UI or API, typically requiring custom date ranges or Boolean filters.

## 18. Export Formats
The Engine must support the following formats:
* **CSV**: For raw data manipulation in Excel/Sheets.
* **JSON**: For programmatic consumption by external APIs.
* **PDF**: For immutable, boardroom-ready presentations.

## 19. Filters
Reports support complex query building (e.g., `Date > X AND Department = Y AND Status = Failed`). The filters applied are permanently stamped onto the final report header for context.

## 20. Search
Generated reports are indexed by metadata (Creator, Date, Category) allowing users to easily find a report generated three months ago without regenerating it.

## 21. Access Control
RBAC is evaluated at the row level during generation. If a Department Admin runs an "Organization Task Report", the Engine silently truncates the result set to only include Tasks from their specific Department.

## 22. Approval
Certain highly sensitive reports (e.g., exporting the entire Audit Ledger for the year) trigger a Guardian policy, forcing the generation request through the Approval Engine before the worker executes it.

## 23. Audit
Every report generation request, successful or failed, is logged to the Audit Ledger. The log includes who requested it, the exact filters applied, and a hash of the generated artifact.

## 24. Monitoring
The Reporting Engine is monitored for queue depth and generation latency. "Stuck" reports must alert system administrators.

## 25. Versioning
Report templates (the SQL/code that generates the report) are versioned. If a metric definition changes, old reports remain untouched, but new reports use the `v2` template.

## 26. Future Expansion
The architecture supports the future addition of "Interactive Reports," allowing users to dynamically pivot and slice cached report data directly within the browser without requesting a new generation.

## 27. Permanent Constraints
* Reports strictly respect RBAC row-level security.
* Reports never expose unauthorized or cross-tenant data.
* The act of generating a report is permanently auditable.
* Reports must be perfectly reproducible (running the exact same parameters for the exact same historical time window must yield identical results).

---

## Never Do

* **Never** generate massive reports synchronously on the main API thread; always use background workers to prevent HTTP timeouts and gateway saturation.
* **Never** embed raw PII, plaintext secrets, or API keys in an exported report.
* **Never** trust client-side filtering to enforce security. If a user is not authorized to see a row, the database query must not return it to the reporting worker.
* **Never** allow a scheduled report to email a secure PDF to an unverified, external email address without explicit Guardian policy approval.

---

## Reporting Constitution
The permanent Reporting principles of AegisAI:
1. **The Principle of Veracity**: A report is a promise of truth. It must perfectly reflect the underlying immutable audit and transactional data, devoid of estimation or hallucination.
2. **The Principle of Bounded Insight**: Knowledge is power, and power is restricted. A user's report is a mirror reflecting only their specific domain of authority.
3. **The Principle of Evidence**: In the enterprise, if it is not documented, it is a rumor. The Reporting Engine translates the digital actions of the AI workforce into undeniable, physical evidence.
