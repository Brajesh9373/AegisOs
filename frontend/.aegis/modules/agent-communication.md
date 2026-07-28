# AegisAI Agent Communication Architecture Specification

This document defines the definitive, permanent Agent Communication Architecture for AegisAI. It establishes the secure, governed routing mechanisms that allow Humans and Agents to exchange information, delegate tasks, and escalate failures, while strictly preventing data leakage and unauthorized access.

## 1. Communication Philosophy
Agents do not possess telepathy, nor do they share a global memory space. In AegisAI, an Agent cannot "just talk" to another Agent. Every message—whether from Human to Agent, or Agent to Agent—is a formal `TaskExecution` event. It must be addressed, routed through the Runtime, inspected by Guardian, and permanently recorded in the Audit Ledger. Communication is physical, governed, and highly restricted.

## 2. Objectives
The Agent Communication Architecture must:
* Decouple the sender from the receiver via the core Task Engine.
* Ensure all intra-agent communication mathematically respects RBAC and Hierarchy boundaries.
* Subject every message payload to Guardian Deep Packet Inspection (DPI).
* Provide a deterministic, auditable trail of how information moved through the workforce.

## 3. Communication Architecture
AegisAI utilizes an Event-Driven Message Bus (RabbitMQ/Kafka) orchestrated by the central Task Engine. Agents do not open direct API connections or sockets to one another. An Agent issues a `SendMessage` tool call to the Runtime. The Runtime validates the request, formats it into an Event, and routes it to the target's queue.

## 4. Human to Agent
The primary initiation vector. A Human User interacts via the Chat UI or an API trigger. The input is wrapped in a `UserInstruction` event, bound to the Human's exact RBAC identity, and queued for the target Agent.

## 5. Agent to Human
Agents cannot randomly message Humans. They can only respond to a thread initiated by a Human, or trigger a formal `Notification` or `ApprovalRequest` based on predefined escalation rules.

## 6. Agent to Agent
Agent A wants to ask Agent B a question. Agent A must execute the `DelegateTask` or `RequestInformation` tool. The Runtime intercepts this, verifies Agent A is allowed to contact Agent B, and if approved, queues the message for Agent B.

## 7. Parent Agent Communication
A Parent Agent orchestrates work by broadcasting or directly assigning tasks to its subordinates. This is a high-bandwidth, trusted path, but is still fully mediated by the Runtime.

## 8. Child Agent Communication
A Child Agent communicates upwards strictly via the `ReturnResult` or `EscalateFailure` events. A Child cannot assign tasks to its Parent.

## 9. Department Communication
Agents within the same Department Workspace can communicate relatively freely, assuming the invoking Agent has been granted permission to access the target Agent via the Builder configuration.

## 10. Cross Department Communication
Highly restricted. An Agent in Marketing cannot directly message an Agent in HR. Cross-department requests must go through an explicitly configured "API Gateway Agent" or trigger a Human Approval workflow to cross the boundary.

## 11. Organization Communication
Impossible. No mechanism exists in the architecture for an Agent in Tenant A to communicate with an Agent in Tenant B.

## 12. Event Based Communication
Agents can subscribe to system events (e.g., `JiraTicketCreated`). When the event fires, the Runtime wakes the Agent and passes the event payload into its context window.

## 13. Request Response
Synchronous-style communication. Agent A asks Agent B for data and explicitly waits (suspends its own execution thread) until Agent B returns the payload.

## 14. Broadcast
A Parent Agent sends a single `UserInstruction` to a group of Child Agents simultaneously (e.g., asking three different research agents to parallelize a literature review).

## 15. Escalation
The formal mechanism for handling unresolvable errors. The Agent halts execution, packages its current state and the exact error, and sends an `Escalation` event up the Hierarchy chain.

## 16. Handoff
Agent A completes Phase 1 of a pipeline and explicitly transfers ownership of the remaining workflow to Agent B, passing along a summarized context block. Agent A then terminates.

## 17. Collaboration
Multiple Agents working in a shared environment. They do not share minds; they share a "Workspace State" (a structured JSON document). They communicate by proposing edits to this shared document via the Runtime.

## 18. Shared Context
When Agent A delegates a task to Agent B, it does not send its entire episodic memory. It uses an internal summarization tool to generate a tight, relevant `Context Payload` to pass to Agent B.

## 19. Context Isolation
Agent B receives the `Context Payload` from Agent A, but Agent B is physically prevented from querying Agent A's internal Vector DB memory space.

## 20. Permission Validation
Before the Runtime routes a message from Agent A to Agent B, it evaluates the RBAC matrix. Does Agent A's Human Owner have permission to invoke Agent B? If not, the message is dropped, and an `Unauthorized` error is returned to Agent A.

## 21. Guardian Validation
The actual text payload of the message is scanned by Guardian. If Agent A attempts to send a Credit Card Number to Agent B, and a policy forbids PII transfer, Guardian blocks the message mid-transit.

## 22. Runtime Integration
The Communication Bus is indistinguishable from the Task Engine. A message *is* a Task.

## 23. Monitoring
The Message Bus emits telemetry. DevOps can monitor the volume of Agent-to-Agent traffic, average latency of delegation, and rate of Guardian interceptions.

## 24. Audit
Every message sent, received, blocked, or escalated is written to the immutable Audit Ledger, including the exact JSON payload.

## 25. Future Expansion
Implementation of standard "Agent Communication Languages" (ACLs) to allow AegisAI agents to securely interoperate with external, third-party agent frameworks via structured APIs.

## 26. Permanent Constraints
*   Agents MUST NEVER open direct P2P network connections to each other.
*   All communication MUST pass through the Runtime/Message Bus.
*   All payloads MUST be validated by Guardian before delivery.
*   Communication MUST mathematically respect the RBAC permissions of the Human Owners.

---

## Communication Flow Examples

**Scenario: Research & Summarize Handoff**
1.  **Human** sends prompt to `OrchestratorAgent`: "Write a report on Q3 Earnings."
2.  `OrchestratorAgent` executes `DelegateTask(target: "DataFetchAgent", prompt: "Get Q3 numbers from DB")`.
3.  **Runtime** intercepts, verifies `OrchestratorAgent` can talk to `DataFetchAgent`. Approves.
4.  `DataFetchAgent` receives task, queries DB, and executes `ReturnResult(payload: "{revenue: 10M}")`.
5.  **Runtime** routes payload back. `OrchestratorAgent` resumes execution.
6.  `OrchestratorAgent` executes `DelegateTask(target: "WriterAgent", prompt: "Draft report using this data: {revenue: 10M}")`.
7.  **Guardian** intercepts payload. Scans for restricted data. Approves.
8.  `WriterAgent` generates report, executes `ReturnResult(payload: "Report text...")`.
9.  `OrchestratorAgent` executes `NotifyHuman(payload: "Report text...")`.
10. **Human** receives the final report in the UI.

---

## Never Do

*   **Never** allow an Agent to pass its full, unredacted context window to another Agent directly; it must be explicitly summarized and passed as a distinct task payload.
*   **Never** allow an Agent to bypass Guardian when talking to another internal Agent, assuming internal traffic is "safe." It is not.
*   **Never** build "backdoors" where Agents share a single underlying database row for memory to simulate shared consciousness. It destroys auditability.

---

## Agent Communication Constitution
The permanent Communication principles of AegisAI:
1. **The Principle of the Mediator**: There is no direct conversation. Every word spoken between digital workers goes through the central switchboard, is recorded, and is subjected to the law.
2. **The Principle of Inherited Silence**: If a Human cannot talk to a specific Department, their Agent cannot talk to that Department. An Agent's voice is only as loud as its owner's security clearance.
3. **The Principle of Contextual Quarantine**: Minds do not merge. Agents exchange discrete, sanitized packages of data. The internal reasoning and memory of an Agent remain a black box to all other Agents on the platform.
