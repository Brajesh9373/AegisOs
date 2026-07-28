# AegisAI Event-Driven Architecture Specification

This document defines the definitive, permanent Event-Driven Architecture for AegisAI. It establishes the rules, lifecycle, governance, and mechanics for how state changes and critical signals are propagated asynchronously across the platform's distributed modules.

## 1. Event Philosophy
An Event represents an immutable fact: something that has already occurred within the platform. The Event-Driven Architecture decouples modules, enabling asynchronous workflows, scalable reacting systems, and perfect historical traceability. Events are the nervous system of AegisAI, communicating truth without assuming execution authority.

## 2. Objectives
The Event Architecture must:
* Decouple domain modules to ensure high availability and scalability.
* Provide an immutable, append-only chronological history of platform state changes.
* Guarantee that cross-module communication is traceable via strict correlation IDs.
* Ensure no event can bypass Guardian or RBAC limits during downstream processing.

## 3. Event Driven Architecture
AegisAI utilizes an asynchronous publish-subscribe model. Domains (e.g., Task Engine, API) publish domain events to an internal Event Bus. Other domains (e.g., Notification Engine, Audit Ledger) subscribe to relevant topics, process the events idempotently, and react accordingly.

## 4. Event Lifecycle
1. **Occurrence**: A domain state changes (e.g., Task is completed).
2. **Creation**: The Domain produces a versioned Event object.
3. **Publication**: The Event is pushed to the Event Bus.
4. **Distribution**: The Bus routes the Event to subscribed queues.
5. **Consumption**: Consumers pop the Event and process it.
6. **Completion**: The Consumer acknowledges successful processing.

## 5. Event Types
Events are categorized based on the domain that triggered them and their operational intent.

## 6. Domain Events
Core business logic state changes. Example: `AgentCreated`, `MemoryArchived`.

## 7. System Events
Platform-level infrastructure or health changes. Example: `DatabaseFailoverInitiated`, `CachePurged`.

## 8. Security Events
Critical indicators of compromise or policy intervention. Example: `GuardianBlockedExecution`, `SuspiciousLoginDetected`.

## 9. Audit Events
Specific events permanently recorded into the compliance ledger, representing human-driven or AI-driven mutations.

## 10. Notification Events
Events explicitly synthesized to alert a human user. Example: `UserMentionedInChat`, `ApprovalRequested`.

## 11. Runtime Events
LLM orchestration signals. Example: `ContextWindowExceeded`, `ToolCallInitiated`.

## 12. Guardian Events
Governance enforcement signals. Example: `PolicyEvaluated`, `RiskThresholdExceeded`.

## 13. Agent Events
Lifecycle changes of AI personas. Example: `AgentSuspended`, `AgentSkillAssigned`.

## 14. Skill Events
Capabilities execution tracking. Example: `SkillVersionDeprecated`, `SkillExecutionFailed`.

## 15. Memory Events
Contextual history alterations. Example: `MemoryCompacted`, `MemoryRestored`.

## 16. Knowledge Events
Document and SOP lifecycle tracking. Example: `KnowledgeCertified`, `KnowledgeArchived`.

## 17. Task Events
Work orchestration tracking. Example: `TaskQueued`, `TaskCancelled`.

## 18. License Events
Entitlement state changes. Example: `LicenseExpired`, `SeatLimitReached`.

## 19. User Events
Human identity tracking. Example: `UserDeactivated`, `UserRoleChanged`.

## 20. Organization Events
Tenant-level mutations. Example: `OrganizationProvisioned`, `OrganizationSuspended`.

## 21. Department Events
Sub-tenant logic. Example: `DepartmentCreated`, `DepartmentBudgetExceeded`.

## 22. Approval Events
Human-in-the-loop tracking. Example: `ApprovalGranted`, `ApprovalExpired`.

## 23. Event Ownership
Events are "owned" by the Domain that produced them. The structure and versioning of the event payload are solely dictated by the producing domain.

## 24. Event Producers
The microservices, background workers, or API controllers that generate events. Producers must never wait for Consumers to finish processing.

## 25. Event Consumers
The background services that listen to the Event Bus. Consumers must be designed to handle duplicate events safely.

## 26. Event Contracts
An Event payload is a strict, versioned contract. Producers cannot arbitrarily change the schema of a published event type without bumping the event version.

## 27. Event Versioning
Events follow semantic versioning. Example: `AgentCreated_v1`. If a breaking change occurs (e.g., removing a field), a new `AgentCreated_v2` is published alongside `v1` until consumers migrate.

## 28. Event Ordering
Absolute global ordering is not guaranteed in distributed systems. Consumers must rely on sequence numbers or timestamps within the event payload to handle out-of-order delivery gracefully.

## 29. Event Idempotency
Consumers must process events idempotently. If an event is delivered twice (at-least-once delivery), the consumer must recognize the Event ID and ensure the system state is not mutated twice.

## 30. Event Correlation
Every event must carry a `CorrelationID` mapping back to the original API request or Task that initiated the causal chain.

## 31. Event Traceability
Traceability ensures that an administrator can look at a final outcome (e.g., a sent email) and trace it back through the Event Bus to the exact user click that started it.

## 32. Event Reliability
The Event Bus must guarantee at-least-once delivery. Events are persisted to disk in the broker until explicitly acknowledged by all subscribed consumer groups.

## 33. Event Retry Strategy
If a consumer fails to process an event (e.g., database timeout), it must not acknowledge the event. The broker will re-deliver the event using an exponential backoff strategy.

## 34. Event Failure Handling
If an event repeatedly fails beyond the maximum retry threshold, it is moved to a Dead Letter Queue.

## 35. Dead Letter Strategy
Events in the Dead Letter Queue (DLQ) trigger critical alerts to platform administrators. The DLQ can be inspected, manually corrected, and re-injected into the Event Bus.

## 36. Event Security
Events in transit must be encrypted. Event schemas must be scrubbed of raw PII or secrets before publication.

## 37. Event Authorization
The Event Bus checks consumer permissions. A module cannot subscribe to an organization's event stream without proper internal system authentication. 

## 38. Event Monitoring
The platform monitors event throughput, processing latency, DLQ depth, and consumer lag.

## 39. Event Auditing
The Audit module is a specialized consumer that listens to all high-privilege event topics and persists them into the immutable WORM (Write Once Read Many) storage.

## 40. Event Retention
The Event Bus retains events temporarily (e.g., 7 days) to allow for consumer replay and recovery. Permanent retention is handled by the Audit domain, not the message broker.

## 41. Event Replay
In the event of a catastrophic consumer bug, developers can point a new consumer group at a historical offset in the Event Bus to replay past events and rebuild state.

## 42. Event Recovery
If an entire data center fails, the Event Bus offsets and replicated event logs are used to restore the exact state of asynchronous workflows in the secondary region.

## 43. Event Scalability
The Event Bus must support horizontal partitioning (sharding) by Organization ID or Workspace ID to ensure high throughput across large multi-tenant deployments.

## 44. Event Compatibility
Producers must add fields gracefully without breaking existing consumers.

## 45. Event Evolution Strategy
When domains evolve, new domain events are introduced rather than retrofitting completely different logic into existing legacy events.

## 46. Future Expansion
The architecture supports future integration with external enterprise Event Buses (e.g., streaming AegisAI events directly to a customer's central Kafka cluster).

## 47. Permanent Constraints
* Events are immutable facts.
* Events never bypass Guardian downstream (processing an event requires authorization).
* Events are append-only.
* Events are versioned.
* Events are organization-aware.

---

## Event Metadata Standards
Every event payload must wrap the domain-specific data in a strict standard metadata envelope.

```json
{
  "event_id": "evt_01HGW...",
  "event_type": "TaskCompleted",
  "event_version": "v1",
  "timestamp": "2026-06-30T12:00:00Z",
  "correlation_id": "req_01HGW...",
  "causation_id": "evt_previous_id",
  "actor": {
    "user_id": "usr_999",
    "agent_id": "agt_888"
  },
  "context": {
    "organization_id": "org_111",
    "workspace_id": "ws_222"
  },
  "data": {
    "task_id": "tsk_777",
    "result": "success"
  }
}
```

* **Event Identity**: `event_id` is a globally unique identifier (e.g., ULID or UUIDv7).
* **Correlation IDs**: `correlation_id` ties all downstream events back to the original request.
* **Causation IDs**: `causation_id` identifies the specific parent event that directly triggered this event.
* **Timestamps**: UTC ISO-8601 format representing the exact moment of occurrence.
* **Organization Context**: The exact tenant boundary.
* **Workspace Context**: The sub-tenant boundary.
* **Ownership Context**: The `actor` block defining exactly who (Human and/or Agent) caused the event.

---

## Conceptual Definitions

* **Event**: An immutable record of something that has already happened.
* **Notification**: A specific type of message designed to alert a human user.
* **Audit**: A legally binding ledger of events used for compliance.
* **Log**: A diagnostic text string used for debugging (not an Event).
* **Task**: A governed unit of pending or active work.
* **Execution**: The act of running a Task or Skill.
* **Workflow**: A chained series of Tasks.
* **Message**: The generic data packet traversing the Event Bus (contains the Event).
* **Signal**: A lightweight, often synchronous indicator (e.g., a hardware interrupt).
* **Trigger**: The condition that spawns a Task or fires an Event.

---

## Naming Conventions
Events must be named as `<Noun><PastTenseVerb>`.
* Correct: `UserAuthenticated`, `MemoryArchived`, `TaskFailed`.
* Incorrect: `AuthenticateUser`, `UpdateMemory`, `TaskError`.

## Enterprise Examples
* **Audit Tracing**: An external Skill fails. The API throws an error. The `SkillExecutionFailed` event is fired. The Audit ledger consumes this and logs the failure. The Notification engine consumes it and emails the Agent Owner. The Task Engine consumes it and marks the parent Task as `Failed`. All actions are tied together by the same `correlation_id`.
* **Multi-Tenant Isolation**: The Event Bus is logically partitioned by `organization_id`. When Org A's Task completes, the `TaskCompleted` event is placed on a partition strictly isolated from Org B, preventing any risk of cross-tenant data processing.

---

## Never Do

* **Never** use Events to execute synchronous business logic that requires an immediate response to the UI.
* **Never** put sensitive plaintext secrets (like passwords or API tokens) inside an Event payload.
* **Never** mutate an Event after it has been published.
* **Never** allow a consumer to assume permissions; consuming an event does not grant the consumer the right to bypass Guardian when acting upon that event.
* **Never** break the `correlation_id` chain; every child action must inherit the parent's correlation ID.
* **Never** design consumers that fail catastrophically if they receive the same `event_id` twice.
* **Never** use Events to bypass the central API contract.

---

## Event Constitution
The permanent Event principles of AegisAI:
1. **The Immutable Truth**: Events represent history. History cannot be changed, deleted, or rewritten.
2. **Total Traceability**: There is no action without an origin. Every ripple in the platform can be traced back to the human who dropped the stone.
3. **Decoupled Governance**: Emitting an event does not guarantee execution. The downstream consumer must always independently verify its right to act on that event through Guardian.
