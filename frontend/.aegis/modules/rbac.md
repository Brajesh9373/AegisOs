# AegisAI RBAC Architecture

This document defines the foundational Role-Based Access Control (RBAC) architecture for AegisAI. It establishes the governance and authorization models that dictate how access is granted, evaluated, and revoked across the platform.

## Objectives
The RBAC architecture is an enterprise-grade authorization system designed to enforce absolute control and accountability. It inherently supports:
* Multi-organization boundaries and isolation.
* Departmental hierarchy and policy segmentation.
* Explicit human ownership of assets and agents.
* Governed AI assistants operating under restricted scopes.
* Human-in-the-loop approval workflows.
* Universal governance and compliance.
* Absolute adherence to the principle of least privilege.
* Seamless future scalability for new features and roles.

## RBAC Philosophy
* **Every action requires authorization**: There is no action, read or write, that bypasses the authorization engine.
* **Permissions are explicit**: Access must be explicitly granted; it is never assumed.
* **Nothing is allowed by default**: A lack of explicit permission equates to a denial.
* **Least privilege**: Users and AI assistants are granted only the absolute minimum access required to perform their current task.
* **Need-to-know access**: Data visibility is strictly compartmentalized based on active context and ownership.
* **Everything is auditable**: Every authorization check and role mutation is permanently recorded.

## Role Hierarchy
The logical role hierarchy represents levels of responsibility rather than explicit permissions:
* **Platform Administrator**: Oversees the entire self-hosted instance, managing global settings, licensing, and overarching security.
* **Workspace Administrator**: Manages high-level integrations and shared environments across multiple organizations if applicable.
* **Organization Administrator**: Holds ultimate authority over a single organization tenant, its policies, users, and global assets.
* **Department Manager**: Governs departmental workflows, approves sensitive actions within the department, and manages team resources.
* **Employee**: A standard human user who executes daily workflows, manages personal agents, and contributes to tasks.
* **AI Assistant**: A delegated computational persona operating strictly within the boundaries of its human owner.
* **Guest**: An external entity with highly restricted, temporary access to a specific shared resource.
* **System Services**: Internal background processors operating under rigid, non-interactive service roles.

## Permission Model
The permission model evaluates access based on the interplay of several concepts:
* **Roles**: Logical groupings of baseline permissions assigned to users.
* **Permissions**: Specific granular rights to perform an action on a resource type.
* **Resources**: The entities (data or functions) being accessed.
* **Actions**: The operation being requested (e.g., read, write, execute).
* **Ownership**: Direct association with a resource, granting elevated implicit authority.
* **Inheritance**: Roles may inherit baseline permissions from parent scopes, but ownership scopes are never implicitly inherited upward.
* **Overrides**: Governance policies that explicitly deny an action, overriding any role-based permission.
* **Delegation**: Temporary assignment of specific permissions to a delegate.
* **Approval**: Contextual escalation requiring human intervention to finalize an otherwise authorized action.

## Ownership Model
Ownership represents the strongest form of localized authority:
* **Users own assistants**: A human user dictates the boundaries, lifecycle, and permissions of their personal agents.
* **Organizations own organizational assets**: Global knowledge, core policies, and audit logs belong exclusively to the organization.
* **Departments own operational assets**: Departmental memory, specific skills, and workflows are owned by the department.
* **Ownership determines authority**: An owner can modify, transfer, or archive their asset. Users cannot manipulate assets they do not own, regardless of their broad role, unless granted explicit administrative override.

## Authorization Flow
Every request evaluates authorization through a strict, linear pipeline:

1. Request
2. ↓ Authentication (Verify caller identity)
3. ↓ Identity Resolution (Map identity to organization and user profile)
4. ↓ Role Resolution (Fetch assigned roles and scopes)
5. ↓ Ownership Validation (Check if the caller owns the target resource)
6. ↓ Permission Validation (Verify explicit granted rights)
7. ↓ Policy Evaluation (Check against global/departmental deny policies)
8. ↓ Approval Check (Determine if human-in-the-loop sign-off is required)
9. ↓ Execution Decision (Permit or Reject)

## Permission Categories
Permissions are logically grouped by action type:
* **View**: Read access to data or metadata.
* **Create**: The ability to instantiate new resources.
* **Update**: The ability to modify existing resources.
* **Delete**: The ability to soft-delete or archive resources.
* **Approve**: The authority to unblock a human-in-the-loop request.
* **Transfer**: The ability to reassign ownership of a resource.
* **Assign**: The right to grant roles or tasks to others.
* **Execute**: The right to invoke a skill, trigger a workflow, or dispatch an agent.
* **Manage**: Administrative rights to configure a domain.
* **Audit**: The right to view the immutable ledger.
* **Export**: The ability to extract data from the platform.
* **Import**: The ability to ingest bulk data into the platform.

## Resource Categories
Resources are the targets of permissions and policies:
* Workspace, Organization, Department, User
* Agent, Skill, Knowledge, Memory
* Task, Notification, Approval
* License, Settings, Audit
* Policies, Monitoring, Runtime, Guardian

## Delegation
Access can be delegated securely:
* **Temporary delegation**: Granting time-bound access to a specific resource or task.
* **Ownership transfer**: Permanent reassignment of an asset from one user/department to another.
* **Role delegation**: Allowing a user to temporarily assume a higher role for incident response or coverage.
* **Department delegation**: Sharing a departmental resource cross-functionally.
* **Revocation**: All delegations can be instantly revoked by the grantor or an administrator.
* **Expiration**: Delegations must support absolute time-to-live (TTL) boundaries.

## Approval Integration
Approvals act as a runtime extension of RBAC, not a replacement:
* **Authorization dictates request eligibility**: A user or agent must first be authorized to *request* an action.
* **Approval extends authorization**: If authorized but flagged by policy as sensitive, the action is paused until an authorized approver signs off.
* **Approval never replaces authorization**: If an agent lacks the base permission to execute a skill, it cannot even request an approval to do so.

## AI Authorization
AI assistants operate under a unique, heavily restricted authorization model:
* **AI inherits ownership**: An AI agent acts on behalf of its human owner.
* **AI never owns permissions**: AI does not have its own distinct RBAC identity; it utilizes a constrained subset of its owner's permissions.
* **AI operates within the owner's permissions**: An AI can never access data its human owner cannot access.
* **AI never escalates privileges**: The execution layer strictly prevents privilege escalation.
* **AI never grants permissions**: AI cannot modify RBAC, delegate access, or approve human-in-the-loop requests.

## Security Principles
* **No privilege escalation**: System architecture prevents lateral or vertical permission escalation.
* **No implicit permissions**: Absence of a deny is not an allow.
* **No anonymous execution**: Every action must be tied to a fully resolved identity.
* **No hidden authorization**: RBAC logic must be centralized and visible; no hardcoded backdoor checks.
* **Everything validated**: Permissions are re-validated at every logical boundary.
* **Everything logged**: Authorization decisions (both allows and denials) are sent to the audit ledger.
* **Everything traceable**: The entire chain of authority (e.g., Agent X acting for User Y via Role Z) must be explicit in logs.

## Audit
Authorization auditing is continuous and immutable:
* **Role changes**: Granting or revoking roles.
* **Ownership transfers**: Changing the owner of an agent, knowledge, or task.
* **Permission changes**: Modifications to the RBAC matrix.
* **Approval history**: Records of who approved or denied a request.
* **Access history**: Logs of sensitive data access.
* All authorization events, especially failures and rejections, must be permanently auditable.

## Future Expansion
The architecture is designed to expand organically:
* New roles can be composed of existing permission primitives.
* New resources automatically integrate into the engine by defining standard Action/Resource mappings.
* New policies can be layered on top of the execution flow without altering the core RBAC resolution logic.

## RBAC Constraints
These constraints govern the implementation of the RBAC engine:
* No hardcoded permissions in application logic (e.g., `if user.name == "admin"`).
* No bypass routes around the centralized RBAC engine.
* No hidden or undocumented roles.
* No direct ownership changes via database manipulation.
* No circular delegation chains.
* No privilege inheritance outside of the strictly defined organizational hierarchy.

## Final Principles
The AegisAI authorization architecture must always prioritize:
**Security**
**Governance**
**Least Privilege**
**Ownership**
**Auditability**
**Maintainability**
**Enterprise Scalability**
