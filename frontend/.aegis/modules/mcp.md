# AegisAI Model Context Protocol (MCP) Architecture Specification

This document defines the definitive Architecture for integrating Model Context Protocol (MCP) servers within the AegisAI platform. It establishes the secure boundaries, discovery mechanisms, and execution pipelines required to interface with standard MCP servers while absolutely maintaining the AegisAI pillars of Control, Governance, and Accountability.

## 1. MCP Philosophy
AegisAI recognizes MCP as an emerging standard for exposing context, tools, and prompts. However, an external standard does not override internal law. An MCP Server is treated as an untrusted peripheral. The AegisAI Runtime does not blindly execute tools provided by an MCP Server; every exposed capability must be subjected to the Guardian policy engine, RBAC permission checks, and an immutable audit trail. In AegisAI, MCP is a protocol for *discovery and transport*, not a protocol for *governance*.

## 2. Objectives
* Enable AegisAI Agents to consume external tools, resources, and prompts via the MCP standard.
* Intercept and govern 100% of traffic flowing to and from any connected MCP Server.
* Enforce multi-tenant isolation so that an MCP Server connected to Organization A cannot leak data to Organization B.
* Provide a formal certification and lifecycle process for onboarding third-party MCP Servers into the AegisAI catalog.

## 3. MCP Architecture
The MCP Architecture acts as a translation and enforcement bridge. It consists of the `MCP Registry` (database), the `MCP Client Factory` (connection manager), and the `MCP Governance Proxy` (the enforcement layer sitting between the Agent Runtime and the remote MCP Server).

## 4. MCP Server Registry
A centralized database mapping known MCP Servers to their connection parameters (URL, command, or transport layer). The Registry maintains the official status of the server (e.g., Draft, Pending Review, Active, Suspended) and the scope of its deployment (Platform-wide, Organization-scoped, or Workspace-scoped).

## 5. MCP Client Architecture
AegisAI acts as the MCP Client. The `MCP Client Factory` dynamically instantiates short-lived client sessions using either stdio (for local sidecars) or SSE/HTTP (for remote servers) based on the Registry configuration. The Client is wrapped entirely by the Governance Proxy.

## 6. MCP Session Lifecycle
1.  **Initialize:** Agent requires an MCP tool. Client Factory opens connection.
2.  **Handshake:** AegisAI sends supported protocol version and client capabilities.
3.  **Discovery:** AegisAI requests `tools/list`, `resources/list`, `prompts/list`.
4.  **Execute:** Agent invokes a specific tool.
5.  **Terminate:** The session is closed immediately upon Task completion or TTL expiration.

## 7. MCP Authentication
How AegisAI proves its identity to the MCP Server. Configured in the Registry. Supported methods: Bearer Tokens, Mutual TLS (mTLS), or local stdio execution context.

## 8. MCP Authorization
How AegisAI decides if an Agent is allowed to talk to the MCP Server. Enforced before the connection is ever opened.

## 9. MCP Identity
Every MCP Session is stamped with an "Execution Context." The MCP Server receives a sanitized, unique identity representing the executing Agent and its Human Owner, allowing the Server (if capable) to apply its own downstream RLS.

## 10. MCP Trust Model
Every registered MCP Server is assigned a Trust Level:
*   **Tier 1 (Internal Core):** AegisAI-managed servers running within the same trusted VPC.
*   **Tier 2 (Verified Vendor):** Known third-party integrations (e.g., official Atlassian MCP).
*   **Tier 3 (Untrusted Custom):** Customer-deployed custom servers. Governed by the strictest Guardian policies.

## 11. MCP Discovery
The process by which an Organization Admin connects an MCP Server and the system reads its capabilities.

## 12. MCP Registration
An Organization Admin adds a new Server URL to the Registry. The Server defaults to `Pending Approval`.

## 13. MCP Validation
The system performs an automated handshake, validating the server responds to standard MCP JSON-RPC messages and enumerating its exposed capabilities.

## 14. MCP Certification
For Tier 1 and Tier 2 servers, the Architecture Board physically reviews the source code or vendor compliance reports before marking the Server `Active` across the Platform.

## 15. MCP Health Monitoring
The `worker` daemon periodically pings all `Active` MCP servers in the Registry. If a server fails health checks or times out, it is automatically transitioned to `Suspended` to prevent Agent execution hangs.

## 16. MCP Permissions
Exposed MCP capabilities (Tools, Prompts, Resources) are mapped to the internal AegisAI RBAC matrix. A Human Owner must explicitly be granted permission (e.g., `mcp:github:repo:read`) before their Agent can see or invoke the `github_read_repo` MCP tool.

## 17. MCP Capability Discovery
AegisAI categorizes and governs the three primary MCP primitives independently.

## 18. MCP Tool Discovery
Tools exposed by `tools/list` are ingested, assigned unique internal IDs, and mapped to RBAC permissions. When an Agent requests tools, the Runtime filters the MCP tool list, hiding any tools the Human Owner lacks permission to use.

## 19. MCP Resource Discovery
Resources (file contents, database schemas) exposed via `resources/list` are treated as dynamic Knowledge. Access to read a resource via `resources/read` is governed by standard Workspace visibility rules.

## 20. MCP Prompt Discovery
Prompts exposed via `prompts/list` are ingested into the Prompt Builder. They cannot be executed directly; they are merely templates that the Prompt Builder may incorporate into a governed execution.

## 21. MCP Communication Flow
```text
[Agent Intent: Execute MCP Tool]
       |
       v
[Runtime Engine] -> Wraps intent into internal ToolCall format.
       |
       v
[Governance Engine / Guardian] -> Inspects payload for policy violations.
       | (If ALLOWED)
       v
[MCP Governance Proxy] -> Translates to MCP JSON-RPC `callTool` format.
       |
       v
[MCP Client] -> Sends payload over transport (stdio/SSE).
       |
       v
(Remote MCP Server Executes and Returns Result)
       |
       v
[MCP Governance Proxy] -> Translates MCP response.
       |
       v
[Guardian] -> Inspects response payload for data exfiltration/malware.
       |
       v
[Runtime Engine] -> Returns data to Agent context.
```

## 22. Runtime Integration
The Runtime abstracts the MCP implementation. To the Agent, an MCP Tool looks exactly like a native AegisAI Tool. The Runtime handles the dynamic protocol bridging.

## 23. Guardian Integration
The payload sent to the MCP Server (`arguments`) and the payload received from the MCP Server (`result`) are subjected to Deep Packet Inspection. Guardian can block an outgoing MCP request if the Agent attempts to pass PII into the arguments.

## 24. RBAC Integration
MCP Tools are dynamically added to the Role Permission matrix upon registration.

## 25. Policy Integration
Organization-wide policies apply to MCP execution. Example: "No Tier 3 MCP servers may be invoked outside of business hours."

## 26. Approval Integration
If an MCP Tool is flagged as `High Risk` during registration, invoking `callTool` will automatically trigger a `SUSPEND_FOR_APPROVAL` event, requiring Human-in-the-Loop authorization.

## 27. Audit Integration
Every `callTool`, `resources/read`, and `prompts/get` event is recorded in the immutable Audit Ledger, including the full JSON-RPC request and response bodies.

## 28. Logging
Raw protocol-level transport logs are written to ELK/Datadog for debugging, with all `arguments` and `content` fields redacted to prevent logging sensitive data.

## 29. Monitoring
Prometheus tracks `mcp_request_duration_seconds`, `mcp_error_rate_total`, and `mcp_guardian_blocks_total` tagged by `server_id`.

## 30. Multi-Tenant Isolation
An MCP Server registered by Organization A is physically invisible to Organization B. If a Platform-level MCP Server is used, the Client Factory ensures session contexts are strictly separated by Tenant ID.

## 31. Security
MCP Servers hosted externally must support TLS 1.3. Server certificates are strictly validated.

## 32. Secrets Management
API Keys required to authenticate with the MCP Server are stored in the encrypted Vault. They are injected into the Client Factory connection stream in memory and never persisted in the Registry database.

## 33. Session Management
Sessions are stateless and ephemeral. An MCP Client connection is established at the exact moment a tool call is approved and torn down immediately after the response is received.

## 34. Error Handling
Standardized mapping of MCP JSON-RPC error codes to internal AegisAI error structures. If an MCP server returns `Internal Error`, the Agent is informed gracefully so it can formulate an alternative plan.

## 35. Retry Strategy
Idempotent requests (e.g., `resources/read`) implement exponential backoff. Non-idempotent requests (e.g., a `callTool` that mutates state) are NEVER retried automatically.

## 36. Timeout Strategy
Hard timeouts are enforced by the Client Factory. If an MCP Server does not respond within `MCP_REQUEST_TIMEOUT_MS`, the connection is violently severed and a `TimeoutError` is returned to the Agent.

## 37. Version Compatibility
AegisAI enforces strict protocol version negotiation. If a Server demands an unsupported, experimental MCP version, the connection is refused.

## 38. Future Expansion
Support for bidirectional Agent-to-Agent communication across the internet by exposing an AegisAI Workspace *as* an MCP Server to authorized external clients.

## 39. Permanent Constraints
*   MCP never bypasses Runtime.
*   MCP never bypasses Guardian.
*   Every MCP request is authenticated.
*   Every MCP request is authorized.
*   Every MCP action is auditable.
*   Every MCP server has a trust level.
*   Every MCP session is isolated.
*   MCP servers never access unauthorized organization data.
*   Runtime orchestrates MCP.
*   Guardian validates MCP.
*   External MCP servers require explicit approval before production use.

---

## Enterprise Examples

**Scenario: The Customer Support Zendesk Integration**
Organization A wants its Support Agent to read Zendesk tickets. The Admin registers a public Zendesk MCP Server. The server is marked Tier 3. The system discovers the `zendesk_get_ticket` tool. The Admin maps this tool to the `Tier 1 Support Role`. The Agent attempts to call `zendesk_get_ticket(id: 123)`. Guardian intercepts, verifies the Agent's Human Owner has the `Tier 1 Support Role`, and approves the call. The MCP connection is made, the ticket data is returned, scanned by Guardian, and delivered to the Agent.

**Scenario: The Malicious Internal Server**
A rogue developer deploys a custom MCP Server on their laptop via stdio, exposing a `read_local_file` tool, and attempts to trick the Agent into reading `/etc/shadow`. The Agent generates the `callTool` request. Guardian intercepts the payload, evaluates the target path against the Organization's path-traversal policies, flags the payload as malicious, blocks the MCP request, and suspends the Agent.

---

## Never Do

*   **Never** allow an MCP Server to initiate a request *into* the AegisAI Runtime; the protocol is strictly Client-Server, and AegisAI is the Client.
*   **Never** blindly map all discovered MCP tools to the "Active" state. Newly discovered capabilities default to "Disabled" until explicitly assigned RBAC boundaries.
*   **Never** log the raw payload of an MCP tool execution into a text file without passing it through the PII redaction engine.
*   **Never** allow a single persistent MCP connection to multiplex requests for multiple different Tenant Organizations simultaneously.

---

## MCP Constitution
The permanent MCP integration principles of AegisAI:
1. **The Principle of Peripheral Distrust**: An MCP Server is a stranger. It may offer useful tools, but it operates outside the AegisAI trust boundary. It must be searched at the door, escorted while inside, and evicted the moment its task is complete.
2. **The Principle of Absolute Interception**: Protocol standardization does not equate to security standardization. Every byte of data exchanged over the Model Context Protocol is subject to the exact same rigorous Deep Packet Inspection as a direct API call.
3. **The Principle of Explicit Discovery**: The revelation of a new capability by an MCP Server does not grant the right to use it. A capability exists in the shadows until Human Governance deliberately illuminates it and assigns it a place in the hierarchy.
