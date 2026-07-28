# AegisAI Organizational Hierarchy Architecture Specification

This document defines the definitive, permanent Organizational Hierarchy Architecture for AegisAI. It establishes the strict, tree-based relational model that dictates ownership, policy inheritance, and data visibility for both human users and AI agents.

## 1. Hierarchy Philosophy
An AI workforce without a clear chain of command is a liability. In AegisAI, an Agent is not an isolated script floating in a vacuum; it is an employee. It belongs to a team, answers to a manager, and operates strictly within the boundaries of its assigned department. The hierarchy is the physical manifestation of accountability. If an Agent fails, the hierarchy dictates exactly which human is responsible.

## 2. Objectives
The Hierarchy Architecture must:
* Establish a rigid, unbroken chain of custody from the Platform root down to the most granular Agent.
* Provide a deterministic mechanism for policy and permission inheritance.
* Prevent horizontal data leakage between departments or organizations.
* Ensure clear escalation paths for Human-in-the-Loop (HITL) workflows.

## 3. Hierarchy Architecture
The hierarchy is an absolute Directed Acyclic Graph (DAG) enforced by Foreign Keys at the database level. Every entity lives within a strictly defined parent boundary.

## 4. Platform Hierarchy
The absolute root of the system. The Platform level is managed by the Super Administrator. It contains global configurations and default system policies that cascade downward.

## 5. Organization Hierarchy
The tenant boundary. Organizations belong to the Platform. An Organization represents a distinct enterprise (e.g., "OmniCorp"). Data cannot cross Organization boundaries under any circumstances.

## 6. Department Hierarchy
Logical divisions within an Organization (e.g., "Finance", "Engineering"). Departments belong to an Organization. They serve as the primary boundary for cost tracking and macro-policy application.

## 7. Workspace Hierarchy
Execution environments that belong to an Organization. Workspaces can optionally be bound to a specific Department. They contain the actual running Tasks, Knowledge bases, and Agent configurations.

## 8. Team Hierarchy
Logical groupings of Human Users within a Department. Teams belong to a Department.

## 9. Human Hierarchy
Humans (Users) belong to an Organization and can be assigned to Teams and Workspaces. Humans are assigned RBAC Roles that dictate their administrative power over the entities below them.

## 10. Agent Hierarchy
Agents belong to a Workspace and, crucially, must have exactly one Human Owner. The Agent inherits the baseline operational limitations of its Human Owner.

## 11. Parent Agent
An Agent configured to act as an orchestrator or manager. A Parent Agent does not execute raw physical tools (like database writing) but instead delegates sub-tasks to Child Agents.

## 12. Child Agent
An Agent configured as a specialist (e.g., "SQL Query Bot"). It receives tasks from a Parent Agent. It reports its results back up the chain.

## 13. Agent Groups
Logical groupings of Agents (Swams) assigned to a specific complex workflow. Agent Groups belong to a Workspace.

## 14. Reporting Structure
`Child Agent` -> `Parent Agent` -> `Human Owner` -> `Department Manager` -> `Organization Admin`. This is the exact flow of accountability.

## 15. Escalation Chain
If a Child Agent encounters a problem it cannot solve, it escalates to its Parent Agent. If the Parent Agent cannot solve it, it suspends the task and escalates to the Human Owner for HITL intervention.

## 16. Ownership Hierarchy
Every digital asset (Agent, Knowledge Document, Workflow) must have a designated human owner or Team owner. Orphaned assets are automatically suspended by the system until ownership is reassigned.

## 17. Permission Inheritance
Permissions are inherited downwards. If a Human Owner lacks permission to execute the `Jira_Write` tool, every Agent owned by that Human is physically blocked from executing that tool, regardless of the Agent's internal configuration.

## 18. Policy Inheritance
Policies cascade downwards and aggregate.
*   **Platform Policy:** "No outbound connections to standard darkweb IP ranges."
*   **Organization Policy:** "No outbound connections except to approved vendors."
*   **Department Policy:** "No usage of GPT-4; use local LLMs only."
An Agent in this Department is bound by all three rules simultaneously. Lower levels can *restrict* further, but they can never *relax* a policy set by a higher level.

## 19. Knowledge Visibility
Knowledge is strictly scoped. A document uploaded to the "Finance Department" Workspace is invisible to Agents operating in the "Marketing Department" Workspace.

## 20. Memory Visibility
An Agent's episodic memory is strictly bound to that Agent. A Manager Agent can query a Child Agent for a summary, but it cannot directly read the Child Agent's raw database memory rows.

## 21. Task Delegation
Tasks can only be delegated downwards or sideways within the same Workspace. A Parent Agent cannot delegate a task to an Agent in a different Workspace.

## 22. Cross Department Collaboration
Agents in different departments cannot directly invoke each other. If Marketing needs an answer from Finance, the Marketing Agent must interact via an explicitly authorized inter-departmental API or HITL request.

## 23. Cross Organization Restrictions
Physically and mathematically impossible via Database Row-Level Security (RLS).

## 24. Hierarchy Visualization
The UI provides a top-down org-chart view of the entire AI and Human workforce, showing exactly who reports to whom and where costs are accumulating.

## 25. Hierarchy Transfer
When a Human Owner leaves the company, their Agents are transferred to their Human Manager. The UI provides a "Bulk Transfer Ownership" wizard.

## 26. Hierarchy Versioning
When an Agent is moved from one Parent to another, or from one Workspace to another, this structural change creates a new Agent Version and triggers an Audit event.

## 27. Hierarchy Audit
Every change to the hierarchy—adding a user to a team, changing an Agent's owner, or moving a Workspace—is permanently logged in the Audit Ledger.

## 28. Future Expansion
Support for "Matrix Management," where an Agent might have a primary structural owner (Engineering) but a temporary project-based owner (Project Alpha Workspace).

## 29. Permanent Constraints
*   Every Agent MUST have exactly one Human Owner.
*   Orphaned Agents MUST be automatically suspended.
*   Policies MUST aggregate downwards; lower levels cannot override higher-level restrictions.
*   Cross-Organization data access is physically impossible.
*   Escalation MUST follow the established reporting chain.

---

## Enterprise Hierarchy Examples

**Scenario: OmniCorp's Support Department**
1.  **Platform:** AegisAI Base System.
2.  **Organization:** OmniCorp.
3.  **Department:** Customer Support.
4.  **Team:** Tier 1 Triage.
5.  **Human Owner:** Alice (T1 Manager).
6.  **Parent Agent:** `TriageOrchestrator` (Owned by Alice).
7.  **Child Agent A:** `PasswordResetBot` (Reports to TriageOrchestrator).
8.  **Child Agent B:** `RefundBot` (Reports to TriageOrchestrator).

*Flow:* A customer emails support. `TriageOrchestrator` reads the email. It realizes it's a refund request. It delegates the task to `RefundBot`. `RefundBot` attempts the refund but hits a policy block (Refund > $500). `RefundBot` escalates to `TriageOrchestrator`. `TriageOrchestrator` recognizes the hard limit and escalates to Alice (Human) via a UI notification.

---

## Never Do

*   **Never** allow an Agent to be created without assigning it to a specific Human or Team.
*   **Never** allow a Workspace Admin to disable an Organization-level Guardian policy.
*   **Never** allow an Agent in the HR department to "search" the general Knowledge Base of the Engineering department.
*   **Never** implement "God Agents" that sit outside the hierarchy; every Agent is subject to the org chart.

---

## Hierarchy Constitution
The permanent Hierarchy principles of AegisAI:
1. **The Principle of Absolute Gravity**: Rules, policies, and restrictions only flow downward. An Agent is bound by the cumulative weight of every rule established above it.
2. **The Principle of the Human Anchor**: AI does not exist in a vacuum. Every action, every token spent, and every database write performed by an Agent is ultimately the legal and operational responsibility of the Human Owner anchored to it.
3. **The Principle of the Glass Walls**: Departments and Workspaces are soundproof glass rooms. You can see the structure from above, but data cannot pass through the walls without an explicit, audited doorway.
