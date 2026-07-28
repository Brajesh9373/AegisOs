# AegisAI Builder Architecture Specification

This document defines the architecture, UX philosophy, and governance mechanics of the AegisAI Builder Suite. The platform provides a highly visual, no-code/low-code experience designed to allow non-technical business leaders to orchestrate an AI workforce, while mathematically ensuring that all configurations strictly adhere to enterprise governance boundaries.

## 1. Builder Philosophy
Building an AI agent should not feel like writing a JSON configuration file. It should feel like onboarding an employee. The Builder experience abstracts complex JSON schemas, OpenAPI specifications, and RAG vector configurations into intuitive, guided, visual flows. However, this abstraction is purely visual; under the hood, the Builder generates deterministic, strongly-typed artifacts that must pass rigorous Guardian validation before activation.

## 2. Objectives
*   Democratize AI orchestration by providing a consumer-grade UX for enterprise-grade tools.
*   Enforce a "Draft -> Review -> Approve -> Publish" lifecycle for all critical configurations.
*   Prevent configuration errors via Live Validation and strict Progressive Disclosure.
*   Ensure every click and configuration change is permanently logged and auditable.

## 3. Builder Architecture
The Builder Suite is a collection of React-based Single Page Applications (SPAs) communicating via REST APIs to the backend. The core architecture relies on an immutable "Draft" state. When a user is in a builder, they are exclusively modifying a temporary JSON blob stored in the `Drafts` table or Redis. Only upon clicking "Publish" does the payload move through the Guardian and into the versioned production tables.

## 4. Visual Builder Principles
*   **Wizard Based:** Complex configurations are broken into linear, digestible steps.
*   **Progressive Disclosure:** Advanced settings (e.g., custom LLM temperature, explicit vector search k-values) are hidden by default behind an "Advanced" toggle.
*   **Visual Hierarchy:** Relationships are represented spatially (e.g., node-based DAGs for Workflows, tree structures for Agent Hierarchy).
*   **Minimal Configuration:** Sensible defaults are provided for everything. A user should be able to click "Next" 5 times and get a working, albeit basic, Agent.

## 5. Guided Builder Experience
The UI explicitly prevents users from entering invalid states. If Step 3 requires a Tool to be selected, the "Next" button to Step 4 is physically disabled until a valid Tool is chosen.

## 6. Progressive Configuration
Instead of presenting a monolithic form with 50 fields, the Builder asks atomic questions. "What is the agent's goal?" -> "What tools does it need to achieve this goal?" -> "Who should review its work?"

## 7. Live Validation
As the user types or drags elements, the frontend asynchronously sends partial payloads to the `/api/v1/guardian/dry-run` endpoint. If a user attempts to give an Agent a tool they do not have RBAC access to, the Builder turns red instantly, explaining *why* it is blocked, rather than failing at the final "Publish" step.

## 8. Auto Save Strategy
Drafts are auto-saved to the server every 5 seconds. Users can safely close the browser and resume building from another device.

## 9. Draft Mode
All Builders operate in Draft Mode until finalized. Drafts have no impact on the active runtime.

## 10. Review Mode
Before Publishing, the Builder presents a "Diff View" summarizing exactly what has changed between the current active version and the new draft.

## 11. Approval Mode
If the user's RBAC role lacks direct publish rights, or if Guardian flags the configuration as "High Risk" (e.g., attaching a destructive Database Skill), the "Publish" button becomes "Submit for Approval."

## 12. Publish Mode
Converts the Draft into an immutable Version record and updates the active pointer, making the new configuration live.

## 13. Versioning
Every publish action creates a new, immutable `Version_ID`.

## 14. Rollback
Every Builder includes a "History" tab. A user can click a previous version and select "Restore to Draft," allowing them to visually inspect the old configuration before republishing it.

## 15. Builder Permissions
Access to specific Builders is governed by RBAC. A Department Manager may have access to the Agent Builder, but only an Org Admin has access to the Policy Builder.

## 16. Builder Audit
Every configuration change, draft creation, and publish event generates an Audit Log record.

## 17. Builder Monitoring
Telemetry tracks where users spend the most time or abandon drafts, allowing continuous UX improvement.

---

## The Builder Suite

### Agent Builder
The core wizard for defining a new digital worker.
1.  **Basic Information:** Name, Avatar, Description.
2.  **Owner:** Which human is responsible for this Agent.
3.  **Department:** Logical grouping for cost and policy inheritance.
4.  **Hierarchy:** Does it report to a Manager Agent? Does it have subordinate Agents?
5.  **Skills:** Selecting capabilities (e.g., "Read Jira," "Send Slack Message").
6.  **Knowledge:** Attaching specific vector-embedded documents.
7.  **Memory:** Configuring episodic memory retention limits.
8.  **Tools:** Explicit API access.
9.  **Prompt:** The core instructions (powered by Prompt Builder).
10. **Policies:** Selecting active Guardian guardrails.
11. **Approval Rules:** Defining HITL requirements.
12. **Review:** Final diff check.
13. **Publish:** Activate.

### Skill Builder
A wizard for defining new external capabilities.
1.  **Discover:** Search community templates or define from scratch.
2.  **Import:** Paste an OpenAPI/Swagger JSON file.
3.  **Validate:** The system parses the schema.
4.  **Test:** Execute a live test against the target API.
5.  **Certification:** Guardian scans the schema for risky endpoints (e.g., `DELETE /users`).
6.  **Approval:** Security team review.
7.  **Publish:** Make available to the Organization.
8.  **Assign:** Grant specific Agents access.

### Prompt Builder
A dedicated interface for engineering the `System` instructions.
*   **Role:** Who are you?
*   **Goal:** What are you trying to achieve?
*   **Responsibilities:** Specific tasks.
*   **Restrictions:** What must you never do.
*   **Context Sources:** Mapping variables like `{{user_name}}`.
*   **Expected Output:** JSON schemas or formatting rules.
*   **Escalation:** When to ask a human for help.

### Workflow Builder
A node-based DAG (Directed Acyclic Graph) editor for defining multi-step, multi-agent processes.
*   Drag and drop nodes (Trigger, Agent Action, Conditional Logic, Human Approval).
*   Connect nodes with visual lines.

### Hierarchy Builder
A highly visual, drag-and-drop org-chart editor for AI Agents.
*   **Flow:** Organization -> Department -> Human Manager -> Parent Agent -> Subordinate Agents.
*   **Support:** Drag & Drop to reassign, Clone, Transfer ownership, Archive.
*   **Dependency Visualization:** Shows which Agents rely on which Skills.
*   **Impact Analysis:** If I delete this Manager Agent, what happens to its 5 subordinates? (The Builder visualizes the orphaned nodes).

### Additional Builders
*   **Knowledge Builder:** Drag-and-drop document upload and chunking configuration.
*   **Memory Builder:** Visualizing and editing an Agent's internal state.
*   **Policy Builder:** Visual logic gates ("IF payload contains X THEN Block").
*   **Approval Builder:** Defining custom routing for HITL requests.
*   **Integration Builder:** OAuth flow configuration for external platforms.
*   **Notification Builder:** Template design for system alerts.
*   **License Builder:** (Admin) Provisioning seats.
*   **Organization/Department/Workspace Builders:** Structural tenant setup.

---

## Playground
Before publishing, the user can test the Agent in a sandboxed Playground attached to the Builder.
*   **Context Preview:** See exactly what data will be injected into the prompt.
*   **Execution Preview:** Run the Agent.
*   **Simulation/Dry Run:** Test against mock data without hitting real APIs.
*   **Result Comparison:** Run the new draft side-by-side against the currently published version to compare outputs.

## Monitoring View
Post-publish, the Builder transforms into a Monitoring View for that entity.
*   **Agent Health:** Success/Error rates.
*   **Queue:** Active tasks.
*   **Memory/Knowledge:** Storage consumed.
*   **Logs & Audit:** Instant access to execution history.

---

## Enterprise Examples & User Journeys

**Scenario: A Marketing Manager needs an Agent to draft weekly social media posts.**
1.  **Start:** The Manager enters the Agent Builder.
2.  **Basic Info:** Names it "SocialBot".
3.  **Prompt:** Types "Draft tweets based on our weekly blog post."
4.  **Knowledge:** Uploads the "Brand Voice Guidelines.pdf".
5.  **Skills:** Selects the "Twitter API" integration.
6.  **Live Validation Warning:** The Builder turns yellow. "Warning: You do not have permission to grant Direct Publish access to Twitter."
7.  **Correction:** The Manager navigates to the Approval Rules step and explicitly adds an "Approval required before Twitter execution" rule.
8.  **Playground:** The Manager pastes a mock blog post. SocialBot drafts a tweet and pauses, simulating the Approval request.
9.  **Publish:** The Manager publishes the Agent.

---

## Never Do

*   **Never** allow a Builder to bypass the backend REST API; the UI must consume the exact same endpoints as an external integration.
*   **Never** allow a user to edit a live configuration directly; every change must start as a Draft and end as a new Version.
*   **Never** hide Guardian rejections; if a configuration is blocked, the UI must explicitly tell the user exactly which policy blocked it and why.
*   **Never** assume technical proficiency; do not expose raw JSON or API headers unless the user clicks "Advanced."

---

## Builder Constitution
The permanent Builder principles of AegisAI:
1. **The Principle of Inevitable Success**: The UI is a funnel designed to physically prevent the user from making a mistake. If a configuration is invalid, illegal, or unauthorized, the interface will not allow it to be submitted.
2. **The Principle of Visual Governance**: Security is not an afterthought hidden in a settings menu. Approvals, policies, and permissions are top-level visual citizens in every Builder flow.
3. **The Principle of the Blueprint**: The Builder does not create life; it creates the blueprint. The Runtime executes the blueprint. The separation between Design (Draft) and Execution (Production) is absolute.
