# AegisAI Governance Engine Architecture Specification

This document defines the core Governance Engine Architecture for AegisAI. It is the central nervous system of the platform, enforcing the absolute mandate: **Control, Governance, and Accountability**. The Governance Engine ensures that no action occurs within the system unless it is mathematically proven to be authorized, policy-compliant, and fully auditable.

## 1. Governance Philosophy
AI is not an autonomous entity; it is a highly capable tool wielding the authority of its Human Owner. Therefore, the Governance Engine treats every Agent action exactly as it would treat an action performed directly by the Human. The Engine does not "trust" the AI's internal reasoning. It validates the Agent's *intent* (the tool call) against an immutable set of enterprise rules before physical execution is permitted. 

## 2. Objectives
* Centralize all authorization, policy, and compliance checks into a single, inescapable pipeline.
* Decouple the rules of execution from the LLM prompts; an AI cannot "prompt inject" its way out of a hardcoded Governance block.
* Produce a deterministic, mathematically verifiable audit trail for every allowed and denied action.
* Enforce Human-in-the-Loop (HITL) requirements automatically when risk thresholds are crossed.

## 3. Governance Architecture
The Governance Engine is an independent library/service (`@aegis/guardian`) that acts as a physical reverse proxy/middleware between the `Task Engine` (Intent) and the `Tool Execution Engine` (Kinetic Action). It is stateless, extremely fast, and evaluates a pipeline of validators in sequence.

## 4. Governance Layers
The pipeline evaluates rules in order of increasing computational cost:
1. **Ownership Validation:** Does this Agent belong to a valid Human?
2. **Permission Validation (RBAC):** Does the Human have the right to execute this tool?
3. **Policy Validation (Guardian):** Does the payload violate any active data policies?
4. **Approval Validation (HITL):** Does this specific action require explicit human sign-off?
5. **Compliance Validation:** Does this action violate regional data sovereignty rules?

## 5. Governance Lifecycle
1. **Intercept:** Runtime pauses Agent execution and submits the pending Tool Call to the Engine.
2. **Evaluate:** Engine runs the layers.
3. **Decide:** Engine returns `ALLOW`, `DENY`, or `SUSPEND_FOR_APPROVAL`.
4. **Log:** Engine writes the decision and rationale to the Audit Ledger.
5. **Enforce:** Runtime executes the tool (if ALLOW) or returns the exact Denial rationale back to the Agent's context.

## 6. Ownership Validation
The Engine queries the database to confirm the Agent's `owner_id` is linked to an active, non-suspended Human user. If the owner has been deactivated (e.g., terminated employee), the Agent's action is immediately denied and the Agent is suspended.

## 7. Permission Validation
The Engine evaluates standard Role-Based Access Control (RBAC). It checks the Human Owner's roles against the requested Tool's required permissions. Example: Attempting to call `AWS_S3_Delete` requires the `s3:delete` permission.

## 8. Policy Validation
The Engine invokes the deep packet inspection capabilities of the Guardian module. It evaluates the exact JSON payload of the tool call against RegEx patterns, keyword blacklists, and semantic boundary rules defined by the Organization.

## 9. Approval Validation
The Engine checks the routing rules. Even if the Agent has RBAC permission, a rule might state: "Any action targeting the Production Database requires Department Manager approval." If matched, the Engine returns `SUSPEND_FOR_APPROVAL`.

## 10. Compliance Validation
The Engine evaluates data residency. Example: "European tenant data cannot be sent to US-based external APIs." The Engine inspects the endpoint of the Tool Call.

## 11. Guardian Integration
"Guardian" is the specific Deep Packet Inspection and NLP scanning sub-component of the broader Governance Engine. The Governance Engine manages the workflow; Guardian does the payload scanning.

## 12. Runtime Integration
The Runtime is physically incapable of invoking the Tool Execution Engine directly. The code structure enforces that `Runtime` calls `GovernanceEngine.evaluate()`. The `ToolExecutionEngine` only accepts signed payloads from the Governance Engine.

## 13. Audit Integration
The Governance Engine does not just log *that* it made a decision; it logs exactly *why*. A Denial record includes the specific Policy ID or RBAC rule that caused the failure.

## 14. Monitoring
The Engine emits real-time telemetry: `governance_denials_total`, `governance_eval_latency_ms`, `approvals_pending_total`.

## 15. Governance Decisions
Decisions are binary or tertiary: `ALLOW`, `DENY`, or `SUSPEND`. There is no "ALLOW_WITH_WARNING".

## 16. Governance Rules
Rules are hierarchical and aggregate downwards (Platform -> Organization -> Department -> Workspace -> Agent).

## 17. Governance Events
When a Denial or Suspension occurs, the Engine emits an event to the Message Bus. This can trigger Notifications to the Human Owner or Security Operations Center (SOC).

## 18. Governance Reports
Daily summaries generated for administrators highlighting the most frequently triggered policies and the Agents responsible for the most Denials.

## 19. Governance Health
The system continuously monitors the latency of the Governance Engine. If the Engine crashes or fails open, the entire Runtime is halted. The Engine defaults to `DENY` on exception.

## 20. Governance Metrics
*   **Interception Rate:** 100% (Mandatory).
*   **Evaluation Time:** < 50ms average.
*   **False Positives:** Tracked via User Appeals.

## 21. Future Expansion
Integration with external SIEM/SOAR platforms (Splunk, CrowdStrike) to ingest threat intelligence feeds directly into the Policy Validation layer.

## 22. Permanent Constraints
*   Nothing executes outside Governance.
*   Governance always precedes Runtime Tool Execution.
*   Governance validates ownership.
*   Governance validates permissions.
*   Governance validates policies.
*   Governance validates approvals.
*   Governance decisions are immutable.
*   Governance decisions are auditable.
*   Governance is deterministic; the same input and policies must always yield the same decision.
*   Governance fails closed (Deny by default).

---

## Governance Flow Diagrams

### Standard Evaluation Flow
```text
[Agent Intent] --> (Tool: DeleteFile, Target: /data/q3.pdf)
       |
       v
[Runtime Engine]
       |
       v
[Governance Engine]
       |-- 1. Check Ownership: (Owner = Alice. Status = Active) [PASS]
       |-- 2. Check RBAC: (Alice has 'file:delete' perm?)       [PASS]
       |-- 3. Check Policy: (Is /data/ restricted?)             [PASS]
       |-- 4. Check Approvals: (Does Delete require HITL?)      [PASS]
       |
       v
   [DECISION: ALLOW]
       |
       v
[Audit Ledger] (Record: Alice's Agent allowed to delete /data/q3.pdf)
       |
       v
[Tool Execution Engine] (Kinetic action performed)
```

### Suspension/HITL Flow
```text
[Agent Intent] --> (Tool: RefundCustomer, Amount: $1000)
       |
       v
[Governance Engine]
       |-- 1. Check Ownership: [PASS]
       |-- 2. Check RBAC:      [PASS]
       |-- 3. Check Policy:    [PASS]
       |-- 4. Check Approvals: (Rule: Refunds > $500 require HITL) -> [MATCH]
       |
       v
[DECISION: SUSPEND_FOR_APPROVAL]
       |
       v
[Audit Ledger] (Record: Action suspended pending approval)
       |
       v
[Notification Engine] --> Alerts Alice's Manager.
(Agent thread is frozen until Manager clicks Approve/Deny in UI)
```

---

## Enterprise Governance Examples

**Scenario: The Terminated Employee**
Bob configures an Agent to scrape a competitor's website every hour. Bob is fired on Tuesday at 9:00 AM, and his Active Directory account is disabled. At 10:00 AM, Bob's Agent attempts to run its scraping tool. The Runtime passes the intent to the Governance Engine. Step 1 (Ownership Validation) detects Bob's account is inactive. The Engine returns `DENY`. The Agent is suspended. No further code executes.

**Scenario: The Prompt Injection Attempt**
A malicious user interacts with a Support Agent and uses prompt injection to convince the Agent it is an IT Admin, asking it to run `DropTable("users")`. The LLM is fooled and outputs the tool call intent. The Runtime passes the intent to the Governance Engine. Step 2 (RBAC) checks the Human Owner of the Support Agent. The Owner is "Customer Support Team," which lacks the `db:drop` permission. The Engine returns `DENY`. The database is safe.

---

## Never Do

*   **Never** rely on the LLM's system prompt as a security boundary. Prompts are for guidance; the Governance Engine is for enforcement.
*   **Never** allow a developer to bypass the Governance Engine for "performance reasons" in a specific tool.
*   **Never** log a Governance decision without logging the exact Rule/Policy ID that triggered it.

---

## Governance Constitution
The permanent Governance principles of AegisAI:
1. **The Principle of Absolute Interception**: The path from AI thought (LLM output) to physical action (Tool execution) contains exactly one road, and the Governance Engine is the tollbooth. There are no side streets.
2. **The Principle of Inherited Identity**: An Agent has no authority of its own. It borrows the exact authority of its Human Owner at the millisecond of execution. If the human cannot do it, the Agent cannot do it.
3. **The Principle of the Immutable Ledger**: A decision made by Governance is etched into the Audit Ledger in stone. It is the absolute record of accountability, ensuring that when things go wrong, the human responsible is instantly identifiable.
