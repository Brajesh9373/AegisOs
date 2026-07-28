# AegisAI Platform Bootstrap Architecture Specification

This document defines the Platform Bootstrap Architecture for AegisAI. It establishes the mechanical sequence of events, validations, and initializations that occur when the platform is launched for the very first time. It ensures that the enterprise environment is securely and deterministically built before any users or AI agents are allowed to interact with the system.

## 1. Bootstrap Philosophy
The initial setup of an enterprise OS is its most vulnerable moment. If foundational security groups, encryption keys, or root administrator accounts are misconfigured at genesis, the entire platform is permanently compromised. Therefore, the Bootstrap sequence is treated as a highly rigid, unskippable, mathematically verifiable state machine. It is not a suggestion; it is the gatekeeper to the platform.

## 2. Objectives
The Bootstrap Architecture must:
* Provide a frictionless, guided installation experience for the initial IT administrator.
* Validate all environmental dependencies (Database, Redis, S3, Network) before allowing configuration to proceed.
* Deterministically seed the database with immutable system defaults (Roles, Permissions, Core Policies).
* Securely establish the initial Root/Super Administrator identity.

## 3. Bootstrap Architecture
The Bootstrap process is a specialized, ephemeral React SPA frontend paired with a locked-down set of backend API endpoints (`/api/v1/setup/*`). When the core API boots, it checks the database for a `system_initialized: true` flag. If false, all standard API routes return a `503 Service Unavailable (System Uninitialized)` error, and the Web container redirects all traffic to the `/setup` wizard.

## 4. Initial System Validation
Before rendering the wizard, the backend validates its own host environment: checking CPU cores, available RAM, disk space, and file permissions.

## 5. License Verification
The user must input an enterprise license key (or a valid Open Source Community token). The system cryptographically verifies the payload. If offline/air-gapped, it validates the local signature.

## 6. Environment Validation
The wizard visually reports the status of necessary `.env` variables required to proceed.

## 7. Database Initialization
The backend connects to PostgreSQL. It automatically runs all Prisma migrations to create the schema, ensuring the database structure matches the code version.

## 8. Storage Validation
The system attempts to write, read, and delete a dummy file in the configured Object Storage (S3/MinIO) to verify bucket permissions.

## 9. AI Provider Validation
The user inputs their initial LLM API keys (e.g., OpenAI, Azure). The system fires a minimal test prompt to verify network egress and authentication.

## 10. SMTP Validation
The user inputs email server details. The system sends a test email to ensure invitations and notifications can be delivered.

## 11. Administrator Creation
The user defines the initial human identity. This user is permanently granted the immutable `Global_Super_Admin` role.

## 12. Workspace Creation
The system prompts the creation of the first Workspace boundary (e.g., "IT Operations").

## 13. Organization Creation
The system prompts the creation of the root Organization entity representing the enterprise tenant (e.g., "OmniCorp").

## 14. Department Creation
The user optionally defines top-level departments (e.g., "Finance", "Engineering").

## 15. Default Policies
The system injects baseline Guardian policies (e.g., "Block execution if token limit exceeded", "Log all destructive tool calls").

## 16. Default Roles
The system seeds the RBAC tables with standard roles (`Org_Admin`, `Dept_Manager`, `Workspace_Admin`, `Agent_Creator`, `Standard_User`).

## 17. Default Permissions
Granular permissions (e.g., `agent:read`, `tool:execute`) are hardcoded and seeded into the database, then mapped to the Default Roles.

## 18. Default Settings
Global variables (session timeouts, password complexity rules, max upload sizes) are initialized.

## 19. Default Agents
The system provisions a "System Assistant" agent, pre-configured to help users learn the AegisAI platform using the documentation.

## 20. Default Skills
Standard system skills (e.g., "Web Search", "Read File") are registered and schema-validated.

## 21. Bootstrap Completion
The `system_initialized` flag is flipped to `true`. The `/setup` routes are permanently disabled. The user is redirected to the Global Dashboard.

## 22. Bootstrap Recovery
If the server crashes during step 7, the system remembers the state. Upon restart, it resumes the wizard exactly where it left off.

## 23. Bootstrap Monitoring
Progress is logged to the console so DevOps engineers can track the initialization in a headless environment.

## 24. Bootstrap Audit
Every action taken during Bootstrap (especially the creation of the Super Admin) is written as the genesis blocks of the Audit Ledger.

## 25. Future Expansion
Support for "Headless Bootstrap" via a declarative `aegis-config.yaml` file, allowing infrastructure-as-code (Terraform/Ansible) to fully initialize the platform without human interaction.

## 26. Permanent Constraints
*   The Bootstrap wizard must run once and only once.
*   Once initialized, the `/setup` API endpoints must reject all traffic.
*   The system must not allow the creation of the Super Admin until the database and storage layers are fully validated.

---

## The Setup Wizard Lifecycle

1.  **Welcome**: "Welcome to AegisAI. Let's configure your enterprise environment."
2.  **License**: Input and cryptographically verify the license key.
3.  **Environment Check**: Green checkmarks for Database, Redis, and File System connectivity.
4.  **Database**: Progress bar as schemas are applied.
5.  **Storage**: Input S3 credentials. System confirms read/write access.
6.  **Administrator**: Create the Root User (Email, Password, MFA setup).
7.  **Organization**: Define the Enterprise Name and Logo.
8.  **Departments**: (Optional) Define structural hierarchy.
9.  **SMTP**: Input mail server details and send a test email.
10. **AI Provider**: Input default OpenAI/Anthropic keys. System runs a test inference.
11. **Review**: Final summary of all configurations.
12. **Initialize Platform**: The system writes the default resources (Roles, Policies, Agents) to the database.
13. **Ready**: Success screen. Redirect to Login.

---

## Validation Rules
*   Every step requires a successful 200 OK from the backend validation ping before the "Next" button enables.
*   If a validation fails (e.g., wrong SMTP password), the user remains on that step with a clear error message.
*   If the user refreshes the page, the API returns the current state, and the UI resumes at the correct step.

---

## Default Resources Created
Upon clicking "Initialize Platform", the backend seeds the following defaults:
*   **Super Admin**: The human user created in Step 6.
*   **Organization**: The root tenant.
*   **Default Departments**: If skipped, a default "General" department.
*   **RBAC**: 5 core roles and 50+ granular permissions.
*   **Policies**: 10 baseline security Guardian rules (Active but set to "Log Only" by default).
*   **Guardian**: Activated and listening.
*   **Runtime**: Activated and listening.
*   **Monitoring**: Base Prometheus metrics initialized.
*   **Audit**: Genesis entries recorded.

---

## Never Do

*   **Never** allow a user to skip the Database or Storage validation steps; assuming infrastructure works leads to catastrophic runtime failures later.
*   **Never** store the LLM API keys in plaintext in the database during Bootstrap; they must be encrypted immediately.
*   **Never** leave the `/setup` routes active after initialization.
*   **Never** allow an existing instance to be "re-bootstrapped" from the UI; resetting the platform requires manual database wiping by a DBA.

---

## Platform Bootstrap Constitution
The permanent Bootstrap principles of AegisAI:
1. **The Principle of Genesis Security**: The first identity created is the most dangerous. The creation of the Root Administrator must be the most heavily validated and audited event in the lifecycle of the software.
2. **The Principle of Proven Ground**: We do not guess if the infrastructure is ready. We attempt to write to the database, we attempt to read from storage, and we attempt to ping the AI. Only physical proof of connectivity allows the installation to proceed.
3. **The Principle of One-Way Doors**: Initialization is a permanent state change. Once the platform is built, the scaffolding is destroyed. The only way to rebuild is to start from zero.
