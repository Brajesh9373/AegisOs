# AegisAI Workflow Architecture Specification

This document defines the definitive, permanent Workflow Architecture for AegisAI. It establishes the rules, state management, and execution orchestration for multi-step processes spanning human and AI agents.

## 1. Workflow Philosophy
A Task is a single unit of work; a Workflow is an enterprise process. Workflows represent complex, deterministic business processes that require state preservation across long periods of time, conditional branching, and handoffs between multiple AI and Human actors. Workflows constrain AI autonomy by enforcing a rigid sequence of allowable operations.

## 2. Objectives
The Workflow Architecture must:
* Orchestrate multi-step, multi-agent, and human-in-the-loop (HITL) processes.
* Preserve perfect state, allowing long-running workflows to sleep and resume without memory loss.
* Guarantee that Guardian evaluates every action at the Workflow layer and the underlying Task layer.
* Provide an immutable execution history for auditing and bottleneck analysis.

## 3. Workflow Architecture
The Workflow Engine sits above the Task Engine. A Workflow is defined as a Directed Acyclic Graph (DAG) of logical Steps. Each Step evaluates preconditions, dispatches a distinct Task to the Task Engine, waits for completion, and then determines the next routing path based on the Task's result payload.

## 4. Workflow Lifecycle
1. **Defined**: The template is created and versioned.
2. **Triggered**: Instantiated by an Event, Schedule, or User.
3. **Running**: The Engine is actively executing the DAG.
4. **Suspended**: Waiting for a human approval, webhook, or timer.
5. **Completed / Failed**: The terminal node is reached.

## 5. Workflow Templates
Workflows are defined as versioned JSON or YAML schemas, explicitly defining nodes, edges, timeout thresholds, and required Agent personas for each step.

## 6. Workflow States
At any given millisecond, a Workflow Execution instance has a discrete state. State is persisted to a high-throughput datastore (e.g., PostgreSQL/Redis) before the next Step is executed, guaranteeing durability.

## 7. Workflow Versioning
Templates are strictly versioned. If a Workflow is actively running `v1`, and a Department Admin publishes `v2`, the running instance completes using the `v1` logic. Only new triggers execute `v2`.

## 8. Workflow Ownership
A Workflow template is owned by a Department or Organization. A specific Workflow *Execution* is owned by the User or System that triggered it. 

## 9. Workflow Execution
The Engine uses a highly concurrent, event-driven pattern (e.g., Temporal or an internal Saga pattern). The Engine dispatches tasks, releases thread resources, and wakes up only when the Event Bus signals that a dependent Task has completed.

## 10. Workflow Approval
A specific Step in a Workflow can be an `ApprovalTask`. The Workflow enters the `Suspended` state until the human Approver explicitly accepts or rejects the payload.

## 11. Workflow Monitoring
Administrators can visualize active Workflows as a live graph in the UI, seeing exactly which node is currently executing, how long it has been running, and where it is bottlenecked.

## 12. Workflow Audit
Every state transition within a Workflow (e.g., `Node A complete, routing to Node B`) is permanently logged to the Audit Ledger.

## 13. Workflow Retry
Steps can define retry policies (e.g., "Retry 3 times with exponential backoff if HTTP 503"). If the retry limit is exhausted, the entire Workflow fails, or triggers a designated `Compensation` (rollback) path.

## 14. Workflow Recovery
If the physical host running the Workflow Engine crashes, the in-flight workflows are automatically recovered by a surviving node based on the last persisted database state. No progress is lost.

## 15. Human Tasks
Workflow Steps that explicitly require a human to input data, review a document, or click a button in the UI.

## 16. AI Tasks
Workflow Steps that dispatch work to a specific AI Agent (e.g., "Agent ReviewBot, summarize this document").

## 17. Mixed Workflows
Processes that interleave AI logic and Human oversight. Example: AI drafts email → Human approves → AI sends email.

## 18. Sequential Workflows
Strict linear progression: Step A must finish before Step B begins.

## 19. Parallel Workflows
Fan-out/Fan-in execution: Step A triggers Steps B, C, and D simultaneously. Step E waits for all three to complete before proceeding.

## 20. Conditional Workflows
Routing based on data: If `Cost > $500`, route to `ApprovalNode`; else, route to `ExecuteNode`.

## 21. Long Running Workflows
Workflows that may take days or months to complete (e.g., an Employee Onboarding process). The Engine gracefully hibernates these instances to conserve compute.

## 22. Scheduled Workflows
Workflows triggered by a CRON expression (e.g., "Run Weekly Security Audit Workflow every Sunday at midnight").

## 23. Event Driven Workflows
Workflows triggered by external webhooks or internal Event Bus signals (e.g., "Trigger Incident Response Workflow when GitHub Repository is marked Public").

## 24. Future Expansion
The architecture supports the future addition of visual drag-and-drop Workflow builders for non-technical business users.

## 25. Permanent Constraints
* Workflows orchestrate tasks; they do not execute business logic themselves.
* The Workflow Engine executes workflows; Guardian validates them.
* Workflows can never bypass Guardian policies or Approval requirements.
* Workflows must be infinitely resumable from their last known state.
* Every state transition is fully auditable.
* Workflow templates are strictly versioned.

---

## Never Do

* **Never** rely on in-memory state variables to track a Workflow's progress; state must be durably persisted to the database before the next step begins.
* **Never** allow an AI Agent to dynamically alter the structure (the DAG) of a running Workflow; the path must be deterministic.
* **Never** build infinite loops into a Workflow without a hard TTL (Time to Live) or iteration limit.
* **Never** allow a Workflow to swallow a Guardian rejection silently; a blocked action must formally fail the Step and escalate.

---

## Workflow Constitution
The permanent Workflow principles of AegisAI:
1. **The Principle of Deterministic Paths**: An AI may think in probabilities, but a business process runs on tracks. Workflows are the iron rails that keep AI execution constrained to expected outcomes.
2. **The Principle of Indestructible State**: An operation that takes a month must survive server crashes, upgrades, and failovers without losing a single byte of context.
3. **The Principle of Explicit Handoff**: A workflow is a chain of custody. When responsibility shifts from an AI to a Human, or from one Agent to another, the handoff must be deliberate, documented, and undeniable.
