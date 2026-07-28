# AegisAI Approval Engine Architecture Specification

This document defines the definitive, permanent Approval Engine Architecture for AegisAI. It establishes the rules, workflows, and governance mechanisms for managing human-in-the-loop (HITL) authorizations across the platform.

## 1. Approval Philosophy
In an Enterprise AI OS, autonomous execution is a risk that must be bounded. The Approval Engine represents the ultimate friction point: where AI velocity yields to human judgment. Approvals are explicit, undeniable transfers of responsibility from an automated system or lower-privileged user to a higher-privileged human authority.

## 2. Objectives
The Approval Architecture must:
* Guarantee that high-risk actions never execute without explicit, cryptographically verifiable human consent.
* Provide flexible workflow routing (serial, parallel, conditional) to match complex organizational hierarchies.
* Prevent approval bottlenecks through governed delegation and escalation.
* Maintain a perfect, unalterable historical ledger of every approval request and decision.

## 3. Approval Architecture
The Approval Engine is a state machine that sits as a middleware component, often invoked by Guardian or the Task Engine. When a Task triggers a policy requiring approval, execution is suspended. The Engine creates an Approval Request, routes it to the designated human(s), and upon final resolution, signals the Task Engine to either resume or abort the operation.

## 4. Approval Lifecycle
1. **Triggered**: Policy evaluation halts execution; Request generated.
2. **Pending**: Request dispatched to Approver(s); Notifications sent.
3. **In Review**: An Approver is actively looking at the request.
4. **Approved / Rejected**: Final cryptographic decision recorded.
5. **Executed**: The original paused operation is resumed or aborted.
6. **Expired / Cancelled**: Request timeout reached or manually aborted.

## 5. Approval Policies
Rules defined within Guardian that dictate *when* an approval is needed (e.g., "Any DB Write requires Manager Approval").

## 6. Approval Rules
The specific routing logic for a triggered policy (e.g., "If risk score > 90, require VP approval").

## 7. Approval Templates
Standardized visual layouts that ensure the Approver sees exactly what is changing (the "Diff"), who requested it, and the potential impact, without ambiguity.

## 8. Approval Levels
Hierarchical tiers of authorization (e.g., L1: Team Lead, L2: Department Head, L3: Security Admin).

## 9. Single Approval
The simplest workflow: exactly one designated user or role must approve the request.

## 10. Multi-Level Approval
A tiered workflow where L1 must approve before L2 is even notified.

## 11. Sequential Approval
A strict chain of specific users who must approve in exact order (User A → User B → User C).

## 12. Parallel Approval
Multiple users are notified simultaneously. The workflow can be configured to require *Any* (first to click approves) or *All* (consensus required).

## 13. Conditional Approval
Dynamic routing based on payload attributes (e.g., "If budget > $10k, route to CFO; else route to Manager").

## 14. Emergency Approval
A "Break Glass" workflow allowing global administrators to instantly override pending approvals during a critical incident. All emergency approvals trigger massive security audits.

## 15. Expiration
Every Approval Request has a strict Time-to-Live (TTL). If not resolved before expiration, the request defaults to "Rejected".

## 16. Escalation
If an Approver does not respond within a configured SLA window, the Engine automatically forwards the request to their supervisor.

## 17. Delegation
Approvers can temporarily delegate their authority to a peer (e.g., during PTO). Guardian logs the delegation, and the delegate assumes the approval right, but the audit log clearly notes the substitution.

## 18. Rejection
Rejection is terminal. The Approver must provide a mandatory rejection reason. The original Task is marked as `Failed` (due to rejection) and cannot be resumed.

## 19. Cancellation
The original requester (or the System) can abort the request before a decision is made, transitioning the state to Cancelled.

## 20. Retry
If a request is Rejected, it cannot simply be "retried". The user must modify the underlying data or context and submit a completely new transaction, generating a new Approval Request.

## 21. Approval Audit
The Engine logs the creation, every state change, and the final decision to the Audit Ledger. The final decision includes the Approver's ID, timestamp, IP, and the exact data payload presented on their screen at the moment of approval.

## 22. Approval Notifications
The Engine triggers the Notification module to dispatch High Priority alerts via In-App, Email, or Chat when a request is Pending, Escalated, or Resolved.

## 23. Approval History
A dedicated UI view allowing users to see all requests they have ever approved or rejected, and allowing requesters to see the status of their submitted requests.

## 24. Approval Security
Approvers must have an active, authenticated session. For highly sensitive requests, the Engine may force a step-up authentication challenge (e.g., requiring an MFA token input) at the exact moment of clicking "Approve".

## 25. Approval Monitoring
Administrators can monitor "Time to Approval" metrics to identify organizational bottlenecks and track SLA compliance.

## 26. Future Expansion
The architecture supports the future addition of AI-assisted Approval Recommendations, where a secondary AI reviews the request and highlights anomalies for the human approver, without holding actual approval authority.

## 27. Permanent Constraints
* Approval never replaces underlying RBAC authorization.
* Approval never bypasses Guardian.
* Expired approvals are permanently invalid.
* Every approval is fully auditable.
* Every approval has a traceable human owner.

---

## Approval Flow Examples

**Parallel (Consensus) Flow:**
1. Agent requests deployment to Staging.
2. Guardian triggers `StagingDeployApproval` policy.
3. Engine routes request to `QA_Team` and `Dev_Lead` simultaneously.
4. `QA_Team` approves. Status: Pending.
5. `Dev_Lead` approves. Status: Approved. Task resumes.

**Sequential Escalation Flow:**
1. Agent requests to delete 500 user records.
2. Guardian triggers `MassDeleteApproval`.
3. Engine routes to `L1_Manager`. TTL set to 2 hours.
4. 2 hours pass. Request escalates to `L2_Director`.
5. `L2_Director` rejects the request, citing "Missing backup verification".
6. Task is terminated. Agent Owner is notified of rejection reason.

---

## Never Do

* **Never** allow an AI Agent to act as an Approver in any workflow. AI can recommend, but human signature is absolute.
* **Never** allow the original requester to approve their own request, even if they hold the necessary role (Strict Separation of Duties).
* **Never** process an approval via an unauthenticated webhook or email reply without a cryptographic signature or strict token validation.
* **Never** present a vague approval prompt (e.g., "Approve Action?"). The UI must explicitly detail the exact diff and target system.
* **Never** leave an approval request pending indefinitely; all requests must have a TTL.

---

## Approval Constitution
The permanent Approval principles of AegisAI:
1. **The Burden of Command**: Approval is not a click; it is the acceptance of legal and operational liability for an action.
2. **Clarity of Consequence**: An approver must never be able to claim, "I didn't know what I was approving." The UI must make the impact undeniable.
3. **Inflexible Delegation**: Authority can be delegated, but accountability cannot. The system meticulously tracks both the original authority and the acting delegate.
