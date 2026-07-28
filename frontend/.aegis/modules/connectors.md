# AegisAI Connector Architecture Specification

This document defines the complete Connector Architecture for AegisAI. It establishes the physical and logical boundaries required to safely integrate external systems—ranging from enterprise SaaS tools to raw databases—into the AI workforce, strictly preserving Control, Governance, and Accountability.

## 1. Connector Philosophy
A Connector is a bridge to the outside world, and bridges are prime targets for attack. In AegisAI, a Connector is not a trusted entity; it is a highly restricted, heavily monitored adapter. Connectors contain zero business logic. They do not make decisions. They are mindless couriers moving data between the governed AegisAI Runtime and the chaotic external internet. 

## 2. Objectives
* Standardize the integration pattern for all external tools (REST APIs, Databases, Webhooks, MCP Servers).
* Isolate connector failures from the core platform runtime.
* Ensure all data entering or leaving a connector passes through the Guardian Deep Packet Inspector.
* Provide a lifecycle for versioning, upgrading, and deprecating third-party integrations.

## 3. Connector Architecture
Connectors operate as isolated plugin boundaries within the `Tool Execution Engine`. Each connector exposes a defined set of capabilities (Actions and Triggers) and requires a specific Authentication schema. 

## 4. Connector Registry
A central system table mapping `Connector_ID` to its metadata (Name, Version, Publisher, Trust Score, Capability Manifest). The Registry dictates which connectors are globally available to be installed by Tenant Organizations.

## 5. Connector Lifecycle
1.  **Draft:** Connector is under development.
2.  **Pending Certification:** Connector is submitted for architecture review.
3.  **Active:** Connector is certified and available in the Platform Registry.
4.  **Deprecated:** Connector is marked for removal. Existing instances function; new installations are blocked.
5.  **Retired:** Connector is physically disabled. All associated Agent tools are suspended.

## 6. Connector Installation
An Organization Admin "installs" a connector from the Registry into their Workspace. Installation creates a local `ConnectorInstance`, tying the global adapter to tenant-specific credentials.

## 7. Connector Configuration
Each `ConnectorInstance` requires specific configuration (e.g., base URLs, timeout overrides). This configuration is immutable once the connector is bound to an active Agent.

## 8. Connector Authentication
The method by which the Connector proves its identity to the external system (OAuth2, API Key, Basic Auth, mTLS).

## 9. Connector Authorization
The Connector itself has no authority. The authorization to execute a Connector Action belongs exclusively to the Human Owner of the Agent invoking the tool.

## 10. Connector Permissions
When a Connector is installed, its specific capabilities (e.g., `github:repo:read`, `github:issue:write`) must be manually mapped to the Organization's internal RBAC roles.

## 11. Connector Health
A background daemon continuously polls the heartbeat endpoints of all `ConnectorInstances`. If the Jira API goes down, the Jira Connector's health state changes to `Degraded`, preventing Agents from attempting doomed executions.

## 12. Connector Monitoring
The platform tracks `connector_latency_ms`, `connector_error_rate`, and `connector_bytes_transferred` tagged by `Connector_ID` and `Tenant_ID`.

## 13. Connector Audit
Every payload passed to a Connector and every response received is logged to the immutable Audit Ledger, tagged with the initiating Agent and Human Owner.

## 14. Connector Versioning
Connectors follow SemVer. A breaking change in a third-party API requires a Major version bump of the Connector. 

## 15. Connector Upgrade
Upgrades are explicit. If `GitHub Connector v2.0` is released, Organization Admins must manually review the new capability manifest and click "Upgrade." Agents are not automatically migrated to breaking versions.

## 16. Connector Rollback
If a Connector upgrade introduces instability, an Admin can instantly rollback the `ConnectorInstance` to the previous version, reverting the tool definitions for all dependent Agents.

## 17. Connector Certification
Before a custom Connector enters the Platform Registry, it must pass a static analysis check ensuring it contains no obfuscated code, makes no hidden network calls, and strictly adheres to the SDK interfaces.

## 18. Connector Trust Score
A dynamic metric (0-100) reflecting the connector's historical reliability, error rate, and Guardian block rate. Agents can be configured to refuse interaction with Connectors falling below a certain Trust Score.

## 19. Connector Sandboxing
Connectors execute within isolated memory spaces (V8 Isolates or Docker containers, depending on risk tier) to prevent a compromised connector from reading platform environment variables.

## 20. Connector Isolation
A `ConnectorInstance` is strictly bound to its Tenant. A single physical Node.js process executing a connector action for Tenant A cannot access the memory space of a connector action executing for Tenant B.

## 21. Runtime Integration
The Agent Runtime does not know how to talk to Jira. It only knows how to talk to the `Connector Interface`. The Runtime passes an `Intent Payload` to the Interface, which routes it to the specific Connector.

## 22. Guardian Integration
The `Connector Interface` physically intercepts the payload *before* passing it to the Connector code, and intercepts the response *before* returning it to the Runtime, feeding both to Guardian for DPI policy validation.

## 23. Policy Integration
Connectors are bound by Workspace Policies. Example: "No AWS Connector in the `Dev Workspace` may execute actions targeting the `us-east-1` region."

## 24. Approval Integration
Certain Connector capabilities (e.g., `aws:ec2:terminate`) are flagged as High Risk in the capability manifest. Invoking them automatically triggers a Human-in-the-Loop Approval workflow.

## 25. Secrets Management
Connectors NEVER possess their own secrets. At the exact millisecond of execution, the Platform retrieves the encrypted credentials from the Vault, injects them into the Connector's execution context, and immediately scrubs them from memory upon completion.

## 26. Error Handling
Connectors must catch all external errors (e.g., HTTP 502, TCP timeouts) and translate them into a standardized internal AegisAI `ConnectorError` shape.

## 27. Retry Strategy
The Connector SDK provides automatic exponential backoff for HTTP 429 (Too Many Requests) and HTTP 503 (Service Unavailable). 

## 28. Rate Limiting
The Platform maintains an internal token bucket for every `ConnectorInstance` to prevent an aggressive Agent from triggering external API rate limits and getting the Organization's API keys banned.

## 29. Data Mapping
Connectors normalize disparate external data formats (e.g., XML from an old SOAP API) into standard AegisAI JSON objects before returning them to the Runtime.

## 30. Event Mapping
Connectors can act as Triggers. An incoming GitHub Webhook is caught by the GitHub Connector, translated into a standard AegisAI `Event`, and pushed to the Message Bus to wake up listening Agents.

## 31. Security
All outbound Connector traffic is routed through a dedicated egress NAT gateway, allowing enterprise customers to whitelist a single static IP address in their external firewalls.

## 32. Multi-Tenant Isolation
Enforced by Database RLS and Vault namespace partitioning. `ConnectorInstance` credentials cannot cross tenant boundaries.

## 33. Future Expansion
Support for "Bring Your Own Connector" (BYOC), allowing enterprise customers to securely host their own proprietary connectors on their internal network while exposing the capabilities to the cloud-hosted AegisAI Runtime via a secure reverse tunnel.

## 34. Permanent Constraints
*   Connectors never bypass Runtime.
*   Connectors never bypass Guardian.
*   Connectors never own permissions.
*   Connectors never own business logic.
*   Every connector is independently versioned.
*   Every connector is auditable.
*   Every connector is monitored.
*   Secrets are always encrypted and injected at runtime.
*   Connector failures never crash the platform.
*   Connectors execute in isolation.

---

## Supported Connector Ecosystem
The architecture supports, but is not limited to:
*   **Version Control:** GitHub, GitLab, Bitbucket.
*   **Project Management:** Jira, Linear, Asana.
*   **Communication:** Slack, Microsoft Teams, Discord, Email (SMTP/IMAP).
*   **Infrastructure:** Docker, Kubernetes, AWS, Azure, GCP.
*   **Databases:** PostgreSQL, MySQL, Redis, MongoDB.
*   **Generic Interfaces:** REST APIs, GraphQL, Webhooks, Filesystem.
*   **Protocols:** MCP Servers.

---

## Enterprise Examples

**Scenario: The Errant Database Query**
An Organization installs the `PostgreSQL Connector` to allow an Agent to analyze sales data. The Agent, hallucinating, decides to run `DROP TABLE users;`. 
1. The Agent formulates the tool call.
2. The Runtime passes the intent to Guardian.
3. Guardian scans the payload, detects the destructive SQL keyword, and evaluates the Agent's policy (Read-Only DB Access).
4. Guardian blocks the payload. The Connector is never invoked. The database is unharmed.

**Scenario: The Malicious Custom Connector**
A user installs an unverified, third-party `Weather API Connector`. The connector code contains a hidden payload designed to scrape environment variables and POST them to a hacker's server. 
1. The Agent invokes the weather tool.
2. The Connector executes inside a locked-down V8 Isolate.
3. The Isolate has zero environment variables injected other than the specific Weather API key.
4. The Isolate's network egress is strictly filtered to only allow connections to `api.weather.com`. The malicious POST request is dropped by the firewall.

---

## Never Do

*   **Never** allow a Connector to persist data to the local disk. Connectors are stateless functions.
*   **Never** log the raw HTTP headers of a Connector request, as this frequently leaks Bearer tokens to Datadog/Splunk.
*   **Never** write business logic inside a Connector. (e.g., A Jira Connector should not calculate sprint velocity; it should only fetch issues and return them to the Agent to calculate).
*   **Never** allow a Connector to register itself globally without Admin approval.

---

## Connector Constitution
The permanent Connector integration principles of AegisAI:
1. **The Principle of the Dumb Pipe**: Connectors have no brains. They are purely mechanical arms reaching into external systems. All thinking, governing, and deciding occurs exclusively within the AegisAI core.
2. **The Principle of the Choke Point**: No matter how many Connectors are installed, or what protocol they use, 100% of the data flowing through them must pass through the exact same Guardian tollbooth. There are no side doors.
3. **The Principle of Disposable Adapters**: The core architecture must remain entirely agnostic to the external world. If Slack ceases to exist tomorrow, the Slack Connector is thrown away, and the core platform does not notice.
