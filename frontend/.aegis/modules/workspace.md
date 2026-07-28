# AegisAI Workspace & Organization Architecture Specification

This document defines the definitive, permanent Workspace & Organization Architecture for AegisAI. It establishes the structural hierarchy, isolation boundaries, and lifecycle management for tenants operating within the platform.

## 1. Workspace Philosophy
AegisAI is built for the enterprise. The enterprise is not a flat list of users; it is a complex, hierarchical structure of isolated units that demand strict data boundaries while allowing governed collaboration. The structural hierarchy (Organization → Department → Workspace) maps directly to legal and operational boundaries.

## 2. Objectives
The Workspace Architecture must:
* Provide absolute cryptographic and logical isolation between multi-tenant Organizations.
* Enable granular, RBAC-governed sub-divisions (Departments and Workspaces).
* Ensure clear ownership of all operational assets (Agents, Knowledge, Tasks).
* Support localized branding, policies, and settings at every hierarchical level.

## 3. Workspace Architecture
The architecture is inherently multi-tenant. Every database query, API route, and Event Bus message is implicitly scoped to the active tenant's context. The hierarchy operates top-down: Platform → Organization → Department → Workspace.

## 4. Organizations
The root tenant entity. An Organization represents a distinct legal entity or overarching corporate body (e.g., "ACME Corp"). It holds the global License, the SSO configuration, and the billing relationship. 

## 5. Departments
A logical division within an Organization (e.g., "Finance", "Engineering"). Departments manage their own budgets (token limits), default Guardian policies, and department-wide Knowledge bases. Organizations own Departments.

## 6. Workspace
A specialized, isolated operational environment within a Department (e.g., "Q3 Audit Project"). Workspaces are where the actual work happens. Agents, Tasks, and Memories are bound to a specific Workspace. Departments own Workspaces.

## 7. Teams
A logical grouping of Users. Teams can span across Workspaces but are contained within an Organization. Teams are primarily used to assign RBAC roles in bulk.

## 8. Users
Human actors authenticated into the system. A User belongs to an Organization and is granted access to specific Departments and Workspaces via RBAC.

## 9. Workspace Ownership
Every Workspace must have at least one explicit Owner (a User). The Owner is responsible for the resources consumed and the actions taken by Agents operating within that Workspace.

## 10. Workspace Lifecycle
1. **Provisioned**: Created by a Department Admin.
2. **Active**: Users are invited, Agents are operating.
3. **Suspended**: Temporarily frozen (e.g., due to budget limits or security alerts).
4. **Archived**: Locked as read-only. No new tasks can execute.
5. **Deleted**: Soft-deleted (retained in Audit logs, but inaccessible to the UI).

## 11. Multi-Tenant Strategy
The platform utilizes a "Shared Compute, Isolated Data" model. All Organizations share the core API and Task Engine workers, but their data is strictly segregated via Row-Level Security (RLS) in the database and isolated prefixes in object storage.

## 12. Isolation
Isolation is mandatory. Data from Organization A can never be queried, leaked, or exposed to Organization B. Even within an Organization, a user in Workspace X cannot view Agents in Workspace Y unless explicitly granted access.

## 13. Branding
Organizations can define White Label settings (logos, primary colors, custom domains). These settings cascade down to Departments and Workspaces unless explicitly overridden.

## 14. Settings
Settings operate on an inheritance model. If a setting is not explicitly defined at the Workspace level, it inherits from the Department, which inherits from the Organization, which inherits from the Platform defaults.

## 15. Policies
Guardian policies also inherit top-down. An Organization can set a mandatory global policy (e.g., "No external emails"). A Workspace cannot override this to be more permissive, but it can add stricter policies (e.g., "No emails at all").

## 16. Defaults
When an Organization is provisioned, the platform establishes secure defaults (e.g., Zero Trust RBAC, MFA enforced).

## 17. Invitations
Users are onboarded via encrypted invitation links or automated SSO Just-In-Time (JIT) provisioning. Invitations are bound to a specific Organization and role.

## 18. Transfers
An Agent or Knowledge document can be transferred between Workspaces within the same Organization (if approved by both Owners). Cross-Organization transfers are strictly forbidden.

## 19. Suspension
An Organization can be suspended by the Platform Admin (e.g., license expiration). This instantly suspends all child Departments, Workspaces, and running Tasks.

## 20. Archiving
When a project is complete, the Workspace is archived. Archived Workspaces do not count against active licensed limits but remain fully searchable for historical audits.

## 21. Monitoring
Tenant resource consumption (Tokens, Storage, API calls) is continuously aggregated at the Workspace level and rolled up to the Organization for billing and throttling.

## 22. Audit
All structural mutations (e.g., changing an Organization's SSO provider, deleting a Workspace) are permanently logged in the global Audit ledger.

## 23. Security
Cross-tenant access is explicitly blocked at the database middleware layer. Every incoming API request's `tenant_id` claim is mathematically validated against the requested resource's `tenant_id`.

## 24. Future Expansion
The architecture supports future integration with "Inter-Tenant Federation," allowing two distinct Organizations to establish a secure, explicit bridge for specific Agents to collaborate on a joint task.

## 25. Permanent Constraints
* The Platform owns Organizations.
* Organizations own Departments.
* Departments own Workspaces.
* Workspaces own Operational Assets (Agents, Tasks).
* Isolation is mandatory.
* Cross-organization access is strictly forbidden unless explicitly authorized by both parties.

---

## Never Do

* **Never** rely solely on application-level `WHERE org_id = X` clauses. Use database Row-Level Security (RLS) to enforce tenant isolation at the deepest possible layer.
* **Never** allow a User to hold an "Organization Admin" role globally if they only require access to a specific Workspace. Enforce least privilege.
* **Never** permit a User to copy or migrate an AI Agent's Memory across the Organization boundary.
* **Never** hard-delete an Organization or Workspace. Always soft-delete to preserve the cryptographic integrity of historical Audit logs.
* **Never** allow a Workspace-level policy to override and weaken a globally enforced Organization policy.

---

## Workspace Constitution
The permanent Workspace principles of AegisAI:
1. **Absolute Boundaries**: Good fences make good neighbors. Multi-tenancy is a privilege of architecture, but isolation is a mandate of security.
2. **Cascading Governance**: Rules flow downhill. The Organization dictates the floor of acceptable behavior; the Workspace can only build a higher ceiling, never a basement.
3. **Unambiguous Ownership**: Every asset lives in a Workspace, and every Workspace has an Owner. There are no orphaned resources in AegisAI.
