# AegisAI Frontend Page Specification

This document defines the complete Frontend Page Specification for AegisAI. It establishes the navigation hierarchy, routing, component structure, and access control for the web-based User Interface.

## Navigation Hierarchy

*   **Authentication** (`/auth`)
    *   Login
    *   MFA Verification
    *   Password Reset
*   **Global Dashboard** (`/`)
*   **Workspaces** (`/workspaces`)
    *   Workspace List
    *   Workspace Dashboard (`/workspaces/:id`)
    *   Workspace Settings (`/workspaces/:id/settings`)
*   **Agents** (`/workspaces/:workspace_id/agents`)
    *   Agent List
    *   Agent Builder (`/workspaces/:workspace_id/agents/new`)
    *   Agent Studio/Chat (`/workspaces/:workspace_id/agents/:agent_id/chat`)
    *   Agent Config (`/workspaces/:workspace_id/agents/:agent_id/config`)
*   **Knowledge Base** (`/workspaces/:workspace_id/knowledge`)
    *   Document Library
    *   Document Viewer (`/workspaces/:workspace_id/knowledge/:doc_id`)
*   **Tasks & Workflows** (`/tasks`)
    *   Task Queue
    *   Workflow Builder (`/workflows/builder`)
    *   Pending Approvals (`/approvals`)
*   **Governance & Security** (`/governance`)
    *   Guardian Policies (`/governance/policies`)
    *   Audit Ledger (`/governance/audit`)
    *   Compliance Dashboard (`/governance/compliance`)
*   **Platform Administration** (`/admin`)
    *   User Management (`/admin/users`)
    *   Role Management (`/admin/roles`)
    *   AI Providers (`/admin/providers`)
    *   Cost Management (`/admin/costs`)

---

## Page Definitions

### 1. Login Page
*   **Purpose:** Authenticate the user and establish the session.
*   **Route:** `/auth/login`
*   **Access Rules:** Public. Unauthenticated users only.
*   **Components:** SSO Buttons, Local Login Form, MFA Prompt Modal.
*   **Actions:** Submit Credentials, Trigger SSO, Submit MFA.
*   **Permissions:** None.
*   **Data Sources:** Identity Provider APIs.
*   **Empty States:** N/A.
*   **Error States:** Invalid Credentials (inline error), Account Locked (modal).
*   **Loading States:** Spinner on submit button.
*   **Related Pages:** Password Reset.

### 2. Global Dashboard
*   **Purpose:** The landing page summarizing activity across all accessible workspaces.
*   **Route:** `/`
*   **Access Rules:** Authenticated users.
*   **Components:** Active Tasks Widget, Pending Approvals Widget, Recent Agents List, Cost Burn Rate Graph (if Admin).
*   **Actions:** Quick-launch Agent, Navigate to Workspace.
*   **Permissions:** View depends on User's assigned Workspaces.
*   **Data Sources:** Aggregated Task metrics, Approvals API, User Profile.
*   **Empty States:** "Welcome! You don't belong to any Workspaces yet. Create one or request access."
*   **Error States:** "Unable to load dashboard widgets." (Skeleton reload).
*   **Loading States:** Shimmer skeletons for widgets.
*   **Related Pages:** Workspace Dashboard, Pending Approvals.

### 3. Workspace List
*   **Purpose:** View and search all available project boundaries.
*   **Route:** `/workspaces`
*   **Access Rules:** Authenticated users.
*   **Components:** Search Bar, Filter Sidebar (Department, Status), Workspace Cards.
*   **Actions:** Create Workspace, Join Workspace.
*   **Permissions:** `workspace:read`. Create action requires `org:workspace:create`.
*   **Data Sources:** Workspaces API.
*   **Empty States:** "No workspaces found matching your search."
*   **Error States:** Standard API failure toast.
*   **Loading States:** Skeleton cards.
*   **Related Pages:** Workspace Dashboard.

### 4. Agent Studio (Chat)
*   **Purpose:** The primary interface for humans to interact with a specific AI Agent.
*   **Route:** `/workspaces/:workspace_id/agents/:agent_id/chat`
*   **Access Rules:** Must be a member of the Workspace.
*   **Components:** Message Thread, Input Box, Tool Execution Panel (side sheet), Context Viewer (side sheet).
*   **Actions:** Send Message, Upload File, View Tool Output, Cancel Task.
*   **Permissions:** `agent:task:execute`.
*   **Data Sources:** WebSocket connection for streaming chat, Task API.
*   **Empty States:** "This is the start of your conversation with SupportBot."
*   **Error States:** "Network disconnected" (Offline banner), "Guardian Blocked Request" (Inline red message bubble).
*   **Loading States:** "Agent is typing..." indicator. Skeleton for tool panel.
*   **Related Pages:** Agent Config, Task Queue.

### 5. Agent Builder/Config
*   **Purpose:** Configure an Agent's persona, prompts, and allowed tools.
*   **Route:** `/workspaces/:workspace_id/agents/:agent_id/config`
*   **Access Rules:** Must be a Workspace Admin or Agent Owner.
*   **Components:** Persona Editor (TextArea), Tool Selector (Drag and Drop), Model Dropdown, Version History Log.
*   **Actions:** Save Draft, Publish Version, Rollback Version, Delete Agent.
*   **Permissions:** `workspace:agent:update`.
*   **Data Sources:** Agent Version API, Skills/Tools Registry.
*   **Empty States:** N/A (Form always populated with defaults or current config).
*   **Error States:** "Validation failed: System prompt is too short."
*   **Loading States:** Full page loading spinner on mount.
*   **Related Pages:** Agent Studio.

### 6. Knowledge Library
*   **Purpose:** Manage documents used for RAG context.
*   **Route:** `/workspaces/:workspace_id/knowledge`
*   **Access Rules:** Workspace Member.
*   **Components:** Dropzone Uploader, Document Data Grid, Semantic Search Bar.
*   **Actions:** Upload File, Delete File, Search Knowledge, View Processing Status.
*   **Permissions:** `workspace:knowledge:read`, `workspace:knowledge:create`.
*   **Data Sources:** Knowledge API.
*   **Empty States:** "No documents uploaded. Drag and drop PDFs here to teach your Agents."
*   **Error States:** "Upload failed: File too large."
*   **Loading States:** Progress bars for active uploads; "Processing Embeddings" badge.
*   **Related Pages:** Document Viewer.

### 7. Pending Approvals
*   **Purpose:** Central hub for Human-in-the-Loop workflow suspensions.
*   **Route:** `/approvals`
*   **Access Rules:** Authenticated users.
*   **Components:** Approval Queue List, Approval Detail Modal (Diff viewer).
*   **Actions:** Approve, Reject, Delegate, Request Clarification.
*   **Permissions:** Must be the explicitly designated Approver for the task.
*   **Data Sources:** Approvals API.
*   **Empty States:** "You have no pending approvals. Zero Inbox achieved!"
*   **Error States:** "Failed to submit approval decision."
*   **Loading States:** Skeleton list.
*   **Related Pages:** Task Queue.

### 8. Guardian Policies (Admin)
*   **Purpose:** Define the security guardrails for the organization.
*   **Route:** `/governance/policies`
*   **Access Rules:** Organization Admins, Compliance Officers.
*   **Components:** Policy Rule Builder (Visual Logic Gates), Scope Selector, Active Policies Data Grid.
*   **Actions:** Create Policy, Disable Policy, Run Dry-Run Simulation.
*   **Permissions:** `org:policy:manage`.
*   **Data Sources:** Policy API, Department Hierarchy API.
*   **Empty States:** "No custom policies defined. Operating on System Defaults."
*   **Error States:** "Logic Error: Policy conditions conflict."
*   **Loading States:** Skeleton grid.
*   **Related Pages:** Audit Ledger.

### 9. Audit Ledger (Admin)
*   **Purpose:** Read-only view of the immutable platform ledger.
*   **Route:** `/governance/audit`
*   **Access Rules:** Organization Admins, Compliance Officers.
*   **Components:** Complex Query Builder (Filters), High-Density Data Grid, JSON Diff Viewer Modal.
*   **Actions:** Search, Filter by Timestamp/Actor/Action, Export to CSV.
*   **Permissions:** `org:audit:read`.
*   **Data Sources:** Audit API.
*   **Empty States:** "No audit events match the current filter criteria."
*   **Error States:** "Query Timeout. Please narrow your search window."
*   **Loading States:** Indeterminate progress bar over grid.
*   **Related Pages:** Compliance Dashboard.

### 10. Cost Management (Admin)
*   **Purpose:** FinOps dashboard tracking AI expenditure.
*   **Route:** `/admin/costs`
*   **Access Rules:** Organization Admins, Finance Roles.
*   **Components:** Burn Rate Line Chart, Spend by Department Pie Chart, Spend by Model Bar Chart, Budget Setting Form.
*   **Actions:** Set Quotas, Export Report.
*   **Permissions:** `org:billing:manage`.
*   **Data Sources:** Cost Engine API.
*   **Empty States:** "No cost data available for this billing period."
*   **Error States:** "Failed to load pricing matrix."
*   **Loading States:** Chart loading skeletons.
*   **Related Pages:** Global Dashboard.
