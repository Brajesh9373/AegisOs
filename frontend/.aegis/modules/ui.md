# AegisAI UI/UX Architecture Specification

This document defines the definitive, permanent UI/UX Architecture for AegisAI. It establishes the design philosophy, interaction principles, navigation structure, and accessibility standards for the enterprise interface.

## 1. Design Philosophy
The AegisAI interface is an enterprise command center. It must inspire trust, guarantee precision, and facilitate rapid decision-making. The design prioritizes data density, clarity, and governed workflows over flashy aesthetics. Consistency is favored over creativity.

## 2. Enterprise UX Principles
* **Predictability**: Users must never guess the outcome of an action.
* **Traceability**: Users must easily understand who did what, and when.
* **Efficiency**: Complex tasks (like Agent creation) are broken down into logical wizards.
* **Transparency**: AI reasoning and Guardian enforcement are surfaced clearly, never hidden.

## 3. Information Architecture
The platform is hierarchically organized to reflect the multi-tenant SaaS reality:
Organization → Department → Workspace → Agents/Tasks/Knowledge.

## 4. Navigation
The primary navigation is a persistent left-hand sidebar containing top-level domains. A secondary contextual top-bar handles search, user profile, notifications, and context switching (e.g., changing Workspaces).

## 5. Dashboard Strategy
Dashboards are designed for triage. They aggregate metrics, pending approvals, and failed tasks at the top, followed by recent activity feeds. They must answer: "What requires my attention right now?"

## 6. Workspace Layout
A Workspace is the primary operational view. It contains a localized dashboard, a list of active Agents, a scoped Knowledge library, and the Task execution queue for that specific project or team.

## 7. Organization Layout
Available only to Tenant Admins. It surfaces billing, cross-department analytics, global Guardian policies, global Audit logs, and user provisioning tools.

## 8. Agent Builder
A multi-step wizard.
* Step 1: Persona & Identity.
* Step 2: Knowledge binding.
* Step 3: Skill provisioning (with Guardian policy warnings).
* Step 4: Review and Submit for Approval.

## 9. Skill Builder
A developer-focused IDE-like interface for writing, testing, and publishing custom integrations. Includes a dual-pane view: code on the left, live test sandbox on the right.

## 10. Knowledge Management
A hierarchical, folder-based view reminiscent of standard enterprise file explorers. Includes clear visual badges indicating Certification status and Expiration dates.

## 11. Memory Management
A read-only chronological timeline allowing users to inspect what an Agent has learned over time, with tools to manually prune or archive obsolete memories.

## 12. Task Management
A Kanban-style or dense tabular view of queued, running, and completed jobs, allowing users to drill down into the Execution Timeline of any specific task.

## 13. Monitoring Dashboard
Real-time graphs displaying token usage, API latency, and LLM provider health.

## 14. Audit Dashboard
A dense, highly filterable, read-only data grid displaying the immutable ledger of all system mutations and Guardian interceptions.

## 15. License Dashboard
A visual breakdown of current limits (Seats, Agents, Workspaces) versus licensed capacity, including the expiration countdown and renewal portal.

## 16. Settings
Grouped into Personal, Workspace, and Organization tiers.

## 17. Forms
Forms are single-column to reduce cognitive load, utilizing clear labeling, inline validation, and descriptive helper text beneath complex fields.

## 18. Tables
Enterprise data grids are the backbone of the UI. They must support resizing, column toggling, multi-column sorting, sticky headers, and bulk-action selections.

## 19. Search
A persistent, global `Ctrl+K` (or `Cmd+K`) omnibar that searches across Tasks, Agents, Knowledge, and Settings simultaneously.

## 20. Filters
Complex views (like Audit or Tasks) use a query-builder interface (e.g., `Status = Failed AND Date > 7 Days`) rather than simple dropdowns.

## 21. Wizards
Used for any process requiring more than 4 inputs or carrying significant risk (e.g., publishing a Global Policy).

## 22. Approval UI
A dedicated "Inbox" for pending requests. The UI must explicitly highlight *what* is being requested, *who* requested it, and the *risk level*, with bold Accept/Reject buttons.

## 23. Notifications
A slide-out panel accessible from the top navigation, segmented into "Unread", "Approvals", and "System Alerts".

## 24. Responsive Design
The UI is mobile-responsive by default, though complex administrative views (like the Agent Builder) degrade to read-only or simplified states on narrow screens.

## 25. Accessibility
WCAG 2.1 AA compliance is mandatory. This includes keyboard navigability, screen-reader compatibility (ARIA roles), and strict color contrast ratios.

## 26. Internationalization
All text strings, date formats, and currency values are extracted into localization dictionaries. Hardcoded English text is forbidden.

## 27. Theming
The UI supports CSS variables for high-level theming (Primary Color, Background, Text) to support Enterprise White Labeling.

## 28. Dark Mode
Native, deeply integrated Dark Mode support. The user's OS preference is respected by default, with a manual override in Personal Settings.

## 29. Design Tokens
Typography, spacing, colors, and shadows are defined as semantic Design Tokens (e.g., `color-danger-bg`) to ensure absolute consistency across components.

## 30. Component Standards
Developers must use the centralized, documented Component Library (e.g., Button, Modal, DataGrid) for all UI construction. Custom one-off components are rejected during PR review.

## 31. Empty States
Empty states must never be blank. They must include an illustration, a brief explanation of what belongs there, and a primary CTA to create the first item.

## 32. Loading States
Use skeleton loaders for content-heavy pages and contextual spinners for localized button actions. Prevent layout shift during loading.

## 33. Error States
Clearly explain what failed, why it failed, and provide an actionable next step or a specific Support ID. Never surface raw JSON or stack traces.

## 34. Future Expansion
The architecture supports the future addition of a drag-and-drop Workflow canvas for visual Task orchestration.

## 35. Permanent Constraints
* Consistency over creativity.
* Enterprise first; consumer aesthetics are secondary to data density.
* Accessibility by default.
* Responsive by default.
* No hidden actions (e.g., relying exclusively on obscure hover states).
* Confirmation modals required before destructive actions.
* Every approval must clearly display the context.

---

## Page Hierarchy

1. **Dashboard** (Global overview)
2. **Workspaces** (List of environments)
   * ↳ Workspace Dashboard
   * ↳ Agents (List & Builder)
   * ↳ Knowledge (Library)
   * ↳ Tasks (Queue & History)
3. **Governance** (Admin only)
   * ↳ Approvals
   * ↳ Policies (Guardian configuration)
   * ↳ Audit Log
4. **Platform** (Admin only)
   * ↳ Users & Roles
   * ↳ Skills Registry
   * ↳ License & Billing
5. **Settings**
   * ↳ Profile
   * ↳ Preferences

---

## User Journey Examples

**Journey: Approving a high-risk Task**
1. Admin receives email notification. Clicks link.
2. Lands directly on the specific Approval Request page.
3. UI presents a diff: "Agent requested to execute `DropTable` on `Customers`. Owner: John Doe."
4. Admin clicks the red "Reject" button.
5. A modal prompts for a mandatory rejection reason.
6. Admin types reason, clicks submit. Returns to Dashboard.

**Journey: Creating a new Agent**
1. User navigates to Workspace -> Agents -> Clicks "New Agent".
2. Wizard Step 1: User names agent "SupportBot".
3. Wizard Step 2: User selects the "Product Manuals" Knowledge folder.
4. Wizard Step 3: User attaches the "Zendesk Reply" Skill.
5. Wizard Step 4: Review. User clicks "Submit for Approval".
6. UI routes to the Agent details page, displaying status as `Pending Approval`.

---

## Never Do

* **Never** use infinite scroll for enterprise data grids; always use deterministic pagination to allow URL linking to specific pages.
* **Never** hide primary actions behind context menus or obscure hover states; if it's important, it must be visible.
* **Never** show a generic "An error occurred" without a correlation ID or a specific reason.
* **Never** use destructive colors (Red) for primary progression actions, even if Red is the enterprise's brand color.
* **Never** release a feature that cannot be entirely operated via keyboard navigation.
* **Never** force the user to memorize IDs; always display human-readable names with the ID available on click or hover.

---

## UI Constitution
The permanent UI principles of AegisAI:
1. **Clarity is Speed**: In an enterprise environment, ambiguity causes errors. The interface must prioritize unmistakable clarity over minimalist aesthetics.
2. **Respect the User's Intent**: If a user clicks a destructive action, verify the intent. If they initiate a long process, preserve their state.
3. **Govern through Design**: The UI must make the safe path the easiest path. Security and governance should feel like natural guardrails, not roadblocks.
