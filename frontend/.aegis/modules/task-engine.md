# AegisAI Task Engine Architecture Specification

This document defines the definitive, permanent Task Engine Architecture for AegisAI. It establishes the rules, lifecycle, governance, and responsibilities for orchestrating asynchronous, synchronous, and scheduled work across the platform.

## 1. Task Philosophy
A Task is a governed unit of requested work. In AegisAI, work is not an invisible background process; it is a formally tracked, owned, and audited entity. The Task Engine acts as the central nervous system coordinating intents from humans, routing them to agents, verifying them through Guardian, and managing their lifecycle.

## 2. Objectives
The Task Engine Architecture must:
* Provide a unified, durable queue for all platform work.
* Ensure every piece of work is explicitly owned by a human.
* Guarantee that execution is fully auditable, resumable, and fault-tolerant.
* Integrate seamlessly with Guardian for security and Runtime for AI execution.

## 3. Task Definition
A Task is a formal database record representing a specific objective (e.g., "Summarize the weekly sales data"), its required context, its assigned executor (Human or Agent), and its current state. 

## 4. Task Architecture
The Task Engine is a stateful, event-driven orchestrator. It sits between the user interfaces (Chat, Web, Email) and the Runtime execution layer. It manages queues, handles state transitions, triggers Guardian checks before state changes, and persists execution artifacts.

## 5. Task Ownership
Every Task has exactly one human Owner and belongs to exactly one Organization. The Owner is legally and operationally responsible for the Task's outcome. If a Task violates policy, the Owner is held accountable.

## 6. Task Lifecycle
The lifecycle of a Task is strictly controlled and linearly progressive:
Draft → Queued → Running → Pending Approval → Completed (or Failed/Cancelled).

## 7. Task States
* **Draft**: Task is being defined; not yet actionable.
* **Queued**: Awaiting worker availability or schedule trigger.
* **Running**: Currently executing via Runtime or awaiting Human input.
* **Pending Approval**: Execution paused, waiting for human-in-the-loop authorization.
* **Suspended**: Execution halted due to an external block or error.
* **Completed**: Successfully finished.
* **Failed**: Terminated due to an unrecoverable error.
* **Cancelled**: Manually aborted by the Owner.

## 8. Task Creation
Tasks are created via explicit triggers. Creation yields a unique Task ID and an initial state of `Queued`.

## 9. Manual Tasks
Created directly via the AegisAI UI (e.g., clicking "Run Report").

## 10. Chat Tasks
Created implicitly when a user asks an Agent to perform a complex or long-running action within a conversation thread.

## 11. Email Tasks
Created when an authorized user emails a specific AegisAI ingestion address with a command.

## 12. Cron Tasks
Scheduled on a recurring time interval (e.g., every Monday at 9 AM).

## 13. Future Event Tasks
Future support for event-driven creation (see Triggers below).

## 14. Task Scheduling
The Task Engine includes a high-precision scheduler that moves Tasks from `Draft` to `Queued` at the exact requested time, respecting timezone configurations.

## 15. Task Priorities
Tasks are assigned priorities (Low, Normal, High, Critical). The Engine prioritizes queue popping based on priority, then age. Critical tasks (e.g., Security Audits) preempt Normal tasks.

## 16. Task Categories
* **Analysis**: Read-only data processing.
* **Mutation**: State-changing operations (requires higher governance).
* **Communication**: Sending emails or notifications.
* **System**: Internal platform maintenance.

## 17. Task Assignment
Tasks are assigned an Executor. 

## 18. Human Assignment
A Task can be assigned to a Human (e.g., a formal request for review). The Task Engine waits for the human to mark it complete.

## 19. Agent Assignment
A Task assigned to an AI Assistant. The Task Engine routes the task to the Runtime to spin up the specific Agent persona.

## 20. Task Approval Workflow
If Guardian flags a Running task as requiring approval (e.g., before writing to a production database), the Task shifts to `Pending Approval`. The Engine pauses execution, alerts the required approver, and resumes only upon cryptographic sign-off.

## 21. Task Validation
Before moving to `Running`, the Engine validates that the Owner is active, the Agent is active, and the Task payload conforms to organizational policies.

## 22. Task Execution Workflow
1. Trigger fires.
2. Task transitions to `Queued`.
3. Worker picks up Task → `Running`.
4. Runtime executes logic.
5. Guardian intercepts Tool usage.
6. If Approval needed → `Pending Approval`.
7. Upon completion, Result generated → `Completed`.

## 23. Runtime Integration
The Task Engine passes the Task ID and contextual payload to the Runtime. The Runtime executes the LLM loop and streams status updates back to the Task Engine.

## 24. Guardian Integration
The Task Engine relies on Guardian to validate every state transition. A Task cannot move from `Queued` to `Running` if Guardian denies it based on RBAC or policy constraints.

## 25. Memory Integration
Tasks read from Organization and Agent Memory for context. Upon `Completed`, the Task Engine writes a summary of the outcome to the Agent's Memory.

## 26. Knowledge Integration
Tasks retrieve certified Knowledge during the execution phase to ground the Agent's reasoning.

## 27. Skill Resolution
The Engine resolves which Skills the assigned Agent is permitted to use for this specific Task, locking down the execution environment.

## 28. Context Generation
The Engine aggregates the Task Prompt, relevant Memory, and permitted Skills, delivering a sanitized context block to the Runtime.

## 29. Task Dependencies
Tasks can depend on other Tasks, forming Directed Acyclic Graphs (DAGs).

## 30. Parent Tasks
A high-level objective containing multiple sub-tasks. A Parent Task is `Completed` only when all Child Tasks complete.

## 31. Child Tasks
Atomic units of work spawned by a Parent Task.

## 32. Blocking Tasks
A Child Task that prevents subsequent Child Tasks from running until it successfully completes.

## 33. Recurring Tasks
Templates that spawn a new unique Task instance every time a Cron trigger fires. The history of all runs is linked to the parent template.

## 34. Retry Strategy
Transient failures (e.g., network timeouts) trigger automatic retries with exponential backoff.

## 35. Failure Handling
Permanent failures (e.g., invalid credentials, Guardian denial) immediately move the Task to `Failed`, alerting the Owner. 

## 36. Timeout Strategy
Every Task has a strict Time-to-Live (TTL). If execution exceeds the TTL, the Engine forcefully terminates it to prevent zombie processes.

## 37. Task Cancellation
Owners can cancel a Task at any time. The Engine intercepts the Runtime, aborts the execution cleanly, and logs the cancellation.

## 38. Task Suspension
An Administrator or Guardian can suspend a Task, freezing its state mid-execution.

## 39. Task Resume
Suspended or `Pending Approval` tasks can be resumed. The Engine re-hydrates the Runtime with the exact state from before the pause.

## 40. Task Transfer
An active Task can be reassigned to a new Owner (e.g., due to PTO). Guardian re-evaluates permissions upon transfer.

## 41. Task History
Every state transition, log line, and tool execution is recorded permanently in the Task History table.

## 42. Task Timeline
A user-friendly visual representation of the Task History, showing when it started, when it paused for approval, and when it finished.

## 43. Task Metrics
The Engine tracks queue latency, execution duration, LLM token usage, and failure rates per Task Category.

## 44. Task Monitoring
Administrators have a real-time dashboard of all `Running` and `Queued` tasks across the organization.

## 45. Task Notifications
The Engine dispatches notifications (UI, Email) on critical state changes (`Failed`, `Pending Approval`, `Completed`).

## 46. Task Audit
The entire lifecycle is mirrored to the immutable Audit ledger. 

## 47. Task Security
Task payloads are encrypted at rest. Users can only query Tasks they own or have departmental rights to view.

## 48. Task Versioning
Recurring Task templates are versioned. If a template is updated, currently running tasks finish under the old version; future tasks use the new version.

## 49. Task Templates
Pre-approved, parameterized workflows (e.g., "Monthly Financial Report Template") that users can instantiate safely.

## 50. Task Governance
Tasks are the primary vehicle for governance. A rogue agent cannot act without a Task, and every Task is bound by Guardian.

## 51. Future Expansion
The Engine is designed to support external Webhooks, API triggers, and enterprise Event Bus (Kafka/RabbitMQ) integrations.

## 52. Permanent Constraints
* Every Task has exactly one owner.
* Every Task belongs to one organization.
* Tasks never bypass governance or Guardian.
* Tasks never bypass ownership or permissions.
* Tasks are fully auditable and traceable.
* Tasks must maintain execution artifacts.

---

## Conceptual Definitions

* **Task**: A governed, tracked unit of requested work.
* **Job**: The underlying physical background process executing the Task.
* **Workflow**: A DAG of multiple connected Tasks (Parent/Child).
* **Execution**: A single attempt at running a Task.
* **Approval**: Human-in-the-loop authorization required to unblock a Task.
* **Runtime**: The execution environment communicating with the LLM.
* **Guardian**: The security perimeter validating the Task.
* **Agent**: The persona assigned to fulfill the Task.
* **Owner**: The human responsible for the Task.
* **Scheduler**: The subsystem managing Cron triggers.
* **Trigger**: The event that creates a Task.
* **Result**: The final structured output of the Task.
* **Artifact**: A file or data blob produced during Task execution.
* **Context**: The payload of Knowledge and Memory provided to the Agent.

---

## Supported Triggers

**Current Triggers:**
* **Manual**: Instantiated via UI click.
* **Chat**: Instantiated via conversation intent.
* **Email**: Instantiated via inbound email parsing.
* **Cron**: Instantiated via time schedule.

**Future Triggers:**
* **Webhook**: HTTP callbacks from external systems.
* **API**: Direct programmatic invocation.
* **Event Bus**: Subscriptions to Kafka/RabbitMQ topics.
* **Queue**: SQS/Azure Service Bus polling.
* **External Integrations**: Salesforce, Jira, or GitHub webhook events.

---

## Lifecycle & State Transition Diagrams

**Logical Lifecycle Flow:**
```
[Trigger] -> (Draft) -> (Queued) -> [Worker Pickup] -> (Running) -> [Guardian Block] -> (Pending Approval) -> [Human Approves] -> (Running) -> [Success] -> (Completed)
```

**State Transition Rules:**
* `Queued` can go to `Running` or `Cancelled`.
* `Running` can go to `Completed`, `Failed`, `Pending Approval`, `Suspended`, or `Cancelled`.
* `Pending Approval` can go to `Running` (Approved) or `Failed` (Rejected).
* `Suspended` can go to `Running` (Resumed) or `Cancelled`.
* `Completed`, `Failed`, `Cancelled` are terminal states.

---

## Enterprise Use Cases & Examples

* **Data Analysis Task**: An executive asks Chat to "analyze Q3 sales". The Chat spawns an asynchronous Task. The user can close their laptop. The Task Engine runs it, and emails the Result later.
* **Scheduled Reporting**: A Cron Task triggers every Friday at 5 PM. It spawns a Parent Task which spins up three Child Tasks to query different databases. When all three finish, a final Child Task formats the Artifact (PDF) and emails the team.
* **Governed Mutation Task**: A user manually triggers a "Clean up stale user accounts" Task. The Agent identifies 50 accounts. Before deleting, Guardian shifts the Task to `Pending Approval`. An Admin reviews the list, clicks Approve, and the Task resumes to delete the accounts.

---

## Never Do

* **Never** allow a background Job to execute without a corresponding governed Task record in the database.
* **Never** allow an Agent to create a Task for another Agent without explicitly inheriting the original Human Owner's ID.
* **Never** permanently delete a Task record; utilize status flags (`Cancelled`, `Failed`).
* **Never** bypass Guardian validation when a Task resumes from a `Suspended` or `Pending Approval` state (permissions may have changed during the pause).
* **Never** execute Tasks in the main synchronous web thread; always offload to asynchronous workers.
* **Never** mix Task execution state with Agent Memory; Memory is historical context, Task State is operational data.

---

## Task Engine Constitution
The permanent Task Engine principles of AegisAI:
1. **Work is Observable**: Nothing happens in the shadows. If an AI thinks, computes, or acts, a Task record tracks it.
2. **Work is Owned**: Every execution utilizes organization resources and carries risk. A human owner is always explicitly attached to that risk.
3. **Work is Governed**: The Task Engine is subservient to Guardian. Execution is a privilege granted moment-by-moment, never guaranteed.
