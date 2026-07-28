# AegisAI Agent Lifecycle Architecture Specification

This document defines the complete operational lifecycle of an enterprise Agent within the AegisAI platform. It governs the states an Agent can inhabit, the transitions between those states, and the strict approval and audit mechanisms required to move an Agent from inception to retirement.

## 1. Lifecycle Philosophy
An Agent in AegisAI is not a script that is simply turned "on" or "off". It is a digital employee. Like a human employee, its lifecycle includes onboarding, probation, active duty, suspension for violations, transfers between departments, and eventual offboarding. The lifecycle is a state machine designed to ensure no Agent executes in production without formal approval and an unbroken chain of accountability.

## 2. Agent States
The system strictly enforces the following immutable states for an Agent entity:

*   **Draft:** The Agent is being configured in the Builder. It does not exist in the active runtime. It cannot execute tools.
*   **Under Review:** The creator has finalized the Draft and submitted it for human review. It is locked from further edits.
*   **Pending Approval:** The review is complete, but final authorization (e.g., from a Department Head or IT Admin) is required before activation.
*   **Approved:** The configuration is mathematically finalized and cryptographically signed, waiting to be turned "Active".
*   **Active:** The Agent is online, polling its queue, and listening for triggers.
*   **Busy:** A sub-state of Active. The Agent is currently executing a Task.
*   **Idle:** A sub-state of Active. The Agent is waiting for a Task.
*   **Suspended:** The Agent is forcefully halted. This occurs automatically via Guardian policy violation, or manually by an Administrator. It cannot process new Tasks.
*   **Disabled:** The Agent is intentionally turned off by its Owner. It remains fully configured but will not respond to triggers.
*   **Archived:** The Agent is removed from active dashboards. Its memory and knowledge bindings are frozen. It can be restored but cannot execute.
*   **Transferred:** A transitional state when an Agent's `owner_id` is changing. Execution is paused until the new owner accepts the transfer.
*   **Retired:** The Agent is permanently decommissioned. Its active API keys are revoked. It cannot be restored.
*   **Deleted (Soft Delete):** The Agent record is marked `deleted_at = NOW()`. It is hidden from all UIs but remains in the database forever for audit purposes.

## 3. Allowed State Transitions
The State Machine enforces strict transition paths:
*   `Draft` -> `Under Review` | `Deleted`
*   `Under Review` -> `Pending Approval` | `Draft` (Rejected)
*   `Pending Approval` -> `Approved` | `Draft` (Rejected)
*   `Approved` -> `Active`
*   `Active` <-> `Busy` | `Idle`
*   `Active` -> `Suspended` | `Disabled` | `Archived` | `Transferred`
*   `Suspended` -> `Active` (Requires Admin Unlock) | `Retired`
*   `Disabled` -> `Active` | `Archived` | `Retired`
*   `Archived` -> `Disabled` (Restoration) | `Retired`
*   `Transferred` -> `Disabled` (Upon acceptance by new owner)
*   `Retired` -> `Deleted`
*   `Deleted` -> (Terminal State)

## 4. Approval Requirements
Transitioning an Agent from `Draft` to `Active` is governed by the Organization's RBAC matrix. If an Agent is granted "Read Only" tools, the Owner may self-approve. If an Agent is granted "Write" tools (e.g., `Update_Production_DB`), the state machine physically blocks activation until a user with the `agent:approve_high_risk` role signs off.

## 5. Ownership Changes
When an Agent is `Transferred`, it immediately drops all running Tasks and enters a frozen state. The receiving Owner must review the Agent's policies and explicitly click "Accept Transfer". Upon acceptance, the Agent enters the `Disabled` state, forcing the new owner to consciously reactivate it under their own authority.

## 6. Memory Behavior
*   **Active/Suspended/Disabled:** Memory is retained and accessible for review.
*   **Transferred:** Episodic memory is wiped to prevent horizontal data leakage between departments, unless explicitly overridden by an Org Admin.
*   **Retired/Deleted:** Memory is cryptographically sealed and retained only for compliance audits. It is severed from the active Vector DB.

## 7. Knowledge Behavior
Bindings to Vector Knowledge Bases are active while the Agent is `Active`. If an Agent is `Transferred` to a new Department, the system automatically unbinds any Knowledge Bases that the new Owner does not have RBAC access to.

## 8. Audit Behavior
Every single state transition generates an immutable `AgentLifecycleEvent` in the Audit Ledger. The record includes the `Agent_ID`, `Previous_State`, `New_State`, `Triggering_User_ID`, and a timestamp.

## 9. Monitoring
The central dashboard displays the global count of Agents by state. Alerting is triggered if an unusually high number of Agents suddenly enter the `Suspended` state, indicating a widespread policy violation or API failure.

## 10. Notifications
State changes trigger notifications.
*   *Owner:* Notified when their Agent is Suspended.
*   *Manager:* Notified when an Agent requires Approval.
*   *SOC:* Notified when an Agent is Retired or Deleted.

## 11. Rollback
If a newly `Approved` version of an Agent exhibits catastrophic failure, the Owner can trigger a `Rollback`. This creates a new Draft based on the previously `Active` version, bypassing standard review if the previous version was already approved.

## 12. Recovery
A `Soft Deleted` Agent can be technically recovered by a Database Administrator, but it will return in the `Draft` state and must pass through the entire Approval lifecycle again before activation.

## 13. Transfer
The Transfer lifecycle ensures continuity of operations when employees change roles or leave the company, re-anchoring accountability to a new human.

## 14. Retirement
Retirement is the formal end-of-life process. All scheduled cron jobs are deleted. All webhook subscriptions are severed. The Agent is rendered inert.

## 15. Permanent Rules
*   An Agent can never jump from `Draft` to `Active` without passing the required Approval gates.
*   A `Suspended` Agent can only be reactivated by a user with equal or higher RBAC privileges than the user/system that suspended it.
*   An Agent cannot be hard-deleted from the database.
*   Transitions are atomic; an Agent cannot be in two states simultaneously.

---

## Lifecycle Diagrams

### The Happy Path
```text
[Builder UI] --> DRAFT 
                   | (Submit)
                   v
             UNDER REVIEW
                   | (Manager OKs)
                   v
           PENDING APPROVAL
                   | (Security OKs)
                   v
               APPROVED
                   | (Owner Clicks 'Start')
                   v
                ACTIVE <-----> BUSY/IDLE
```

### The Termination Path
```text
                ACTIVE
                   | (Owner Leaves Company)
                   v
              TRANSFERRED
                   | (New Manager Accepts)
                   v
               DISABLED
                   | (Project Ends)
                   v
               RETIRED
                   | (Compliance Data Retention Met)
                   v
               DELETED (Soft)
```

### The Violation Path
```text
                ACTIVE 
                   | (Agent attempts to exfiltrate PII)
                   v
     [Guardian Intercepts & Blocks]
                   |
                   v
               SUSPENDED
                   | (Security Team Investigates & Modifies Prompts)
                   v
                 DRAFT
```

---

## Enterprise Examples

**Scenario: The Errant Intern**
An intern builds a "Stock Trading Bot" and attempts to attach the corporate brokerage API keys. Because the Agent's requested tools are flagged as High Risk, the Agent enters `Pending Approval`. The Finance Director receives an alert, reviews the Agent configuration, and clicks `Reject`. The Agent reverts to `Draft` state. The intern is physically unable to activate it.

**Scenario: The Infinite Loop**
An `Active` Agent gets stuck in a logic loop, repeatedly calling a paid third-party API and burning through the department's budget. The Billing Daemon detects the spike and triggers an automatic state change to `Suspended`. The Agent's current execution thread is instantly killed. The Owner is notified and must fix the underlying prompt before requesting reactivation.

---

## Never Do

*   **Never** allow a Developer to manually change an Agent's state in the database to bypass the Approval workflow.
*   **Never** delete an Agent's execution history when the Agent is Retired or Deleted; accountability outlives the asset.
*   **Never** allow an Agent in the `Suspended` state to finish its current task. Suspension is a hard `SIGKILL`.

---

## Agent Lifecycle Constitution
The permanent Lifecycle principles of AegisAI:
1. **The Principle of Linear Authorization**: An Agent is guilty until proven innocent. It must earn its right to exist in the active runtime by passing through a rigid, sequential corridor of human and systemic approvals.
2. **The Principle of Instant Paralysis**: The platform reserves the absolute right to instantly, violently, and without warning rip an Agent from the `Active` state to the `Suspended` state if a policy is breached.
3. **The Principle of Eternal Memory**: Agents may be turned off, retired, and deleted from the UI, but their existence and their actions are permanently etched into the immutable ledger. An Agent never truly dies; it just stops moving.
