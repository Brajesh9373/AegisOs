# AegisAI Tool Management Architecture Specification

This document defines the definitive, permanent Tool Management Architecture for AegisAI. It establishes the rules, execution pathways, and governance models for the functional primitives (Tools) that Agents use to interact with the world.

## 1. Tool Philosophy
A Tool is the mechanical hand of an Agent. An Agent may reason, but a Tool executes. Tools must be fundamentally "dumb" and deterministic; they accept parameters, perform a single action, and return a result. All intelligence resides in the Runtime, and all security resides in Guardian.

## 2. Objectives
The Tool Architecture must:
* Provide a standardized, strongly-typed interface for all executable actions.
* Ensure tools are intrinsically safe by stripping them of independent decision-making.
* Guarantee that every tool execution is intercepted by Guardian before execution.
* Support seamless discovery and binding of tools to Agents at runtime.

## 3. Tool Architecture
A Tool consists of a JSON Schema (defining inputs and outputs) and an Execution Handler (the code that performs the action). The Runtime dynamically injects the Tool's JSON schema into the Agent's prompt context. If the LLM requests a tool execution, the Runtime catches the request, passes the payload to Guardian for policy evaluation, and if approved, invokes the Execution Handler.

## 4. Internal Tools
Tools natively built into the AegisAI platform (e.g., `SearchKnowledgeBase`, `CreateTask`, `ReadMemory`). They execute within the core API process boundaries but are still subject to Guardian checks.

## 5. External Tools
Tools provided by third-party Plugins or Integrations (e.g., `JiraCreateTicket`). These execute via the Plugin SDK in isolated sandboxes or via the Egress Proxy.

## 6. MCP Tools
Tools dynamically discovered from Model Context Protocol (MCP) servers. The architecture natively parses MCP manifests and proxies the tool execution request to the external MCP server over standard transports.

## 7. HTTP Tools
Generic tools allowing an Agent to make REST or GraphQL calls to arbitrary endpoints, heavily governed by strict domain whitelists in Guardian.

## 8. Database Tools
Tools allowing SQL execution. These are hyper-restricted, requiring mandatory Approval workflows for any mutative (`UPDATE`, `DELETE`, `DROP`) statements, and are bound by Row-Level Security.

## 9. CLI Tools
Tools executing shell commands. These operate strictly inside ephemeral, unprivileged, network-isolated container sandboxes.

## 10. SDK Tools
Language-specific functions (Python, Node.js) executed via a serverless function runner (e.g., AWS Lambda, OpenFaaS) to allow custom enterprise logic.

## 11. Tool Registry
A centralized database mapping all available Tools to their underlying Integration or Plugin provider. The registry acts as the source of truth for a Tool's schema and version.

## 12. Tool Discovery
When a Task begins, the Runtime queries the Registry to assemble the final list of Tools the assigned Agent is permitted to use, injecting their schemas into the context window.

## 13. Tool Permissions
Tools do not "have" permissions. A Tool cannot bypass RBAC. The *User* or *Agent* invoking the tool holds the permissions. Guardian evaluates if the *invoker* is allowed to use the *tool* with the *requested parameters*.

## 14. Tool Ownership
Every Tool is owned by the Organization or Department that registered it. Modifications to a Tool's schema or Execution Handler require Owner approval.

## 15. Tool Execution
1. LLM outputs a Tool Call JSON.
2. Runtime parses the JSON.
3. Runtime sends `(Invoker, Tool, Parameters)` to Guardian.
4. Guardian evaluates policies (`Allow`, `Deny`, `RequireApproval`).
5. If allowed, Runtime routes the payload to the specific Execution Handler (Internal, Egress Proxy, or Sandbox).
6. Result is returned, formatted, and injected back into the LLM context.

## 16. Tool Validation
The Runtime strictly validates the LLM's requested parameters against the Tool's JSON schema before sending the payload to Guardian. Invalid payloads are rejected immediately with a schema error sent back to the LLM for self-correction.

## 17. Tool Certification
Third-party or highly mutative tools must be marked as `Certified` by a global administrator before they can be attached to any Agent in a production Workspace.

## 18. Tool Monitoring
The Runtime tracks execution latency, success/failure ratios, and timeout frequencies for every Tool.

## 19. Tool Audit
Every single tool execution is permanently logged in the Audit Ledger. The log includes the Invoker ID, Tool ID, raw input parameters, execution latency, and the raw output result.

## 20. Tool Health
Background workers periodically ping the Execution Handlers (especially for External/HTTP tools) to verify availability. Unhealthy tools are temporarily masked from Agent discovery to prevent deterministic failure loops.

## 21. Tool Versioning
Tools are strictly versioned. Modifying a tool's schema creates a `v2`. Agents explicitly bind to specific major versions to prevent upstream changes from breaking established workflows.

## 22. Tool Compatibility
If a Tool requires an Integration (e.g., `GitHubCreateIssue`), it cannot be executed unless the Workspace has a valid, active authentication token for that specific Integration.

## 23. Tool Lifecycle
Registered → Tested → Certified → Active → Deprecated → Archived.

## 24. Tool Isolation
The execution of a Tool must never be capable of crashing the main AegisAI Runtime. All external or custom code tools run in isolated processes or containers.

## 25. Tool Security
Tools must never log secrets or sensitive parameters to standard output. The Execution Handler must scrub sensitive data before returning the result to the Runtime, preventing the LLM from inadvertently memorizing API keys.

## 26. Future Expansion
The architecture supports the future addition of "Tool Chaining," where a highly optimized, deterministic sequence of tools can be executed synchronously without returning to the LLM for intermediate reasoning, drastically reducing token costs.

## 27. Permanent Constraints
* Tools never bypass Runtime orchestration.
* Tools never bypass Guardian evaluation.
* Tools never own their own permissions; the invoker does.
* Tools must be independently testable via the UI.
* Tools are infinitely replaceable modules.
* Tool execution is permanently auditable.
* Tool health and latency are continuously monitored.

---

## Never Do

* **Never** build business logic or branching decisions directly into a Tool. A Tool performs one action. If branching is needed, the LLM must make the decision based on the Tool's output.
* **Never** allow a Tool to evaluate its own security constraints. Guardian is the only arbiter of authorization.
* **Never** return an unhandled stack trace or raw HTML error page from a Tool back to the LLM. All tool errors must be caught and normalized into a clean string (e.g., "Error: Upstream timeout").
* **Never** execute a CLI or script-based Tool on the same host operating system as the core AegisAI database or API.

---

## Tool Constitution
The permanent Tool principles of AegisAI:
1. **The Principle of Obedience**: A tool is a mechanism, not a mind. It does exactly what it is told, nothing more, and nothing less.
2. **The Principle of Interception**: There is no direct line between an Agent's thought and the outside world. Every action passes through the tollgate of Guardian.
3. **The Principle of Accountability**: The Tool is never to blame. The Agent that chose to use it, the Guardian that allowed it, and the Human that authorized it bear the absolute responsibility for the outcome.
