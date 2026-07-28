# AegisAI Skill Architecture Specification

This document defines the definitive, permanent Skill Architecture for AegisAI. It establishes the rules, lifecycle, governance, packaging, and execution model for all executable capabilities available to AI agents within the platform.

## 1. Skill Philosophy
Skills are the physical actuators of the AegisAI platform. While Knowledge represents what an agent knows, Skills represent what an agent can *do*. Skills are isolated, reusable, and strictly governed blocks of executable logic that bridge the gap between AI reasoning and real-world system mutation.

## 2. Objectives
The Skill Architecture must:
* Standardize the creation, packaging, and distribution of executable capabilities.
* Ensure all skill invocations are unbreakably mediated by Guardian.
* Guarantee backward compatibility and strict versioning for enterprise stability.
* Enable a secure, auditable ecosystem for first-party and third-party integrations.

## 3. Skill Definition
A Skill is a cohesive, versioned package of executable Tools designed to achieve a specific domain objective (e.g., "GitHub Integration"). A Skill defines its inputs, outputs, validation rules, and required permissions without holding any intrinsic authority.

## 4. Skill Architecture
Skills are stateless, decoupled modules loaded dynamically by the Runtime. They expose a standardized manifest of Tools to the AI. When an AI decides to use a Tool, the Runtime intercepts the intent, passes the payload to Guardian for authorization, and only upon approval does the Runtime invoke the Skill's execution logic.

## 5. Skill Categories
Skills are categorized by their origin and trust level to enforce varied governance workflows.

## 6. Official Skills
Built, signed, and maintained by the AegisAI core team. These are universally trusted and shipped with the platform (e.g., core File System manipulation, Audit Logging).

## 7. Organization Skills
Built by the enterprise tenant for their specific internal systems (e.g., a custom internal CRM integration). Fully trusted within the tenant's boundaries.

## 8. External Skills
Third-party integrations or community-built packages. These operate in a zero-trust sandbox and require rigorous inspection before use.

## 9. Custom Skills
Ad-hoc scripts or temporary integrations created by an agent or user for immediate use. These are restricted to the lowest privilege execution environment.

## 10. Skill Registry
The centralized, tenant-scoped ledger tracking all registered Skills, their current versions, certification statuses, and deployment histories.

## 11. Skill Package Structure
Every Skill must conform to a standardized logical package structure, ensuring predictable deployment and execution.
* **Manifest** (Mandatory): Declares name, version, description, and the list of exposed Tools.
* **Metadata** (Mandatory): Author, tags, category, and minimum platform version.
* **Configuration** (Mandatory): Expected environment variables, secrets, and connection parameters.
* **Execution Logic** (Mandatory): The actual code or API mapping that performs the work.
* **Validation Rules** (Optional): Input sanitization schemas (e.g., JSON Schema).
* **Instructions** (Optional): Text-based hints injected into the agent's prompt on how to best use the skill.
* **Tests** (Optional): Standardized verification scripts.
* **Documentation** (Optional): Human-readable usage guides.

## 12. Skill Metadata
Metadata ensures discoverability. It is strictly separated from execution logic and used by the Runtime to decide which skills to inject into the agent's context window.

## 13. Skill Versioning
Skills adhere to strict Semantic Versioning (SemVer). The platform supports side-by-side deployment of multiple versions. Agents are bound to specific minor versions to prevent unapproved breaking changes.

## 14. Skill Dependencies
Skills must declare dependencies on other Skills or specific platform runtime capabilities. Circular dependencies are strictly forbidden.

## 15. Skill Compatibility
Skill manifests must declare compatibility bounds (e.g., "Requires AegisAI Platform v2.0+"). The registry rejects incompatible uploads.

## 16. Skill Certification
A formal badge indicating a Skill has passed organizational security audits, code reviews, and E2E testing. 

## 17. Skill Trust Score
A dynamic metric reflecting a Skill's error rate, frequency of policy violations, and community/tenant rating. High-risk actions from low-trust skills automatically trigger human approval.

## 18. Skill Testing
Skills must be independently testable in a mock environment without requiring a live LLM or active Guardian connection.

## 19. Skill Validation
At invocation, inputs provided by the LLM are validated against the Skill's defined schema. Invalid payloads are rejected before Guardian evaluation.

## 20. Skill Publishing
Moving a Skill from development to the active Registry, making it available for assignment to agents.

## 21. Skill Import
The governed process of ingesting an External Skill into the tenant Registry. Imports require administrative authorization.

## 22. Skill Export
Packaging an Organization Skill for distribution. Secrets and tenant-specific configurations are automatically stripped.

## 23. Skill Marketplace
A future-proof concept for a secure, organization-level or global hub to discover and share certified Skills.

## 24. Skill Approval Workflow
Certain Skills (e.g., those requiring DB write access) require multi-stage management approval before they can be assigned to an active Agent.

## 25. Skill Lifecycle
Draft → Testing → Certified → Stable → Deprecated → Archived.

## 26. Draft Skills
Under active development. Can only be invoked by the authoring user in a specialized sandbox.

## 27. Testing Skills
Deployed to the Registry for E2E testing but not available for general agent assignment.

## 28. Certified Skills
Audited and approved for production use.

## 29. Stable Skills
Certified skills that have demonstrated long-term reliability and are recommended for widespread use.

## 30. Deprecated Skills
Flagged for removal. New agents cannot be assigned this skill, and existing owners are notified to migrate.

## 31. Archived Skills
Permanently disabled. Execution attempts instantly fail. Code is retained for historical audit correlation.

## 32. Skill Permissions
Skills do not hold intrinsic RBAC permissions. They define *required* permissions. Guardian checks if the invoking Agent's Owner possesses those permissions before execution.

## 33. Skill Ownership
Every Skill in the Registry is owned by a User, Department, or the System. The owner is responsible for maintenance and security patches.

## 34. Skill Maintenance
Owners are alerted if their Skill exhibits high failure rates or violates updated governance policies.

## 35. Skill Execution Model
Skills execute synchronously or asynchronously. The Runtime handles the execution loop and returns the result (or a background task ID) to the agent.

## 36. Skill Runtime Integration
The Runtime exposes the Skill's capabilities to the LLM via tool-calling APIs (e.g., OpenAI functions). 

## 37. Skill Guardian Integration
Guardian acts as the proxy between the Runtime and the Skill execution environment. It intercepts the payload, validates ownership and policy, and either blocks or forwards the request.

## 38. Skill Memory Integration
Skill executions and their results are automatically written to the Agent's Working Memory and the Audit ledger.

## 39. Skill Knowledge Integration
Skills may query the Knowledge base (e.g., a "Search SOPs" skill) but they do not mutate Knowledge without explicit publication workflows.

## 40. Skill Context Integration
Only the schemas and instructions of *assigned* and *active* Skills are injected into the agent's prompt context.

## 41. Skill Monitoring
The platform tracks execution latency, error rates, and invocation frequency per Skill.

## 42. Skill Metrics
ROI metrics analyze time saved by comparing Skill execution times against manual human baselines.

## 43. Skill Audit
Every Skill invocation logs the Skill ID, Version, Input Payload, Output Payload, Agent ID, and Guardian decision to the immutable ledger.

## 44. Skill Security
Skills execute in isolated sandboxes or via locked-down API gateways. They cannot access the platform's root database or filesystem directly.

## 45. Skill Distribution
Skills are distributed as versioned immutable packages (e.g., zip files or container images).

## 46. Skill Upgrade Strategy
Upgrades are explicit. Agents are pinned to a Skill version. Owners must explicitly click "Upgrade" to bind the agent to the new version, ensuring predictable behavior.

## 47. Skill Rollback Strategy
If a new Skill version causes failures, the owner can instantly rollback the agent to the previous pinned version.

## 48. Skill Deprecation Policy
Skills must undergo a mandatory deprecation grace period (e.g., 90 days) before Archival, allowing dependent workflows to be updated safely.

## 49. Future Expansion
The architecture supports future concepts like autonomous Skill synthesis (agents writing their own temporary skills), which will be confined to ultra-restrictive, ephemeral sandboxes.

## 50. Permanent Constraints
* Skills are stateless logic blocks.
* Skills never bypass Guardian.
* Skills never possess their own RBAC permissions.
* Skills operate only through Runtime orchestration.
* Skills must be versioned.

---

## Conceptual Definitions

* **Skill**: A bundled package of executable capabilities (e.g., "GitHub Integration").
* **Tool**: A single, specific function within a Skill (e.g., "Create Pull Request").
* **Knowledge**: Static organizational truth.
* **Memory**: Dynamic conversational and operational history.
* **Prompt**: The text instruction sent to the LLM.
* **Runtime**: The execution engine that parses the LLM output and orchestrates Skill invocation.
* **Workflow**: A predefined sequence of Agent and Skill interactions.
* **Agent**: The persona invoking the Skill.
* **Capability**: The logical authorization to perform an action.
* **Provider**: The external system the Skill interacts with (e.g., AWS, Jira).
* **Execution**: The physical act of running the Skill's code.

---

## Skill Examples

* **Infrastructure Skill**: `KubernetesManager` - Tools: `RestartPod`, `ScaleDeployment`. Requires Admin approval.
* **Developer Skill**: `GitOperations` - Tools: `Commit`, `Push`, `CreateBranch`.
* **Finance Skill**: `InvoiceProcessor` - Tools: `ReadInvoicePDF`, `SubmitToERP`.
* **HR Skill**: `OnboardingAutomation` - Tools: `CreateEmailAccount`, `ProvisionSlack`.
* **Monitoring Skill**: `DataDogQuerier` - Tools: `GetErrorSpikes`, `CheckServiceHealth`.
* **Custom Skill**: `WeeklyReportCompiler` - Ad-hoc Python script created by a user to format specific CSVs.
* **External Community Skill**: `WeatherLookup` - Low-risk, third-party API integration.
* **Official Platform Skill**: `AegisMemoryManager` - Core platform tool for updating Agent Memory.

---

## Never Do

* **Never** allow a Skill to directly query the core AegisAI database bypassing the platform APIs.
* **Never** allow a Skill to execute without Guardian intercepting the request payload.
* **Never** overwrite an existing Skill version; always publish a new semantic version.
* **Never** embed raw API keys or secrets inside the Skill execution code.
* **Never** allow an External Skill to bypass the Import/Certification workflow.
* **Never** grant a Skill intrinsic authority to bypass human-in-the-loop approvals.
* **Never** allow Skills to mutate their own manifest or version definitions at runtime.

---

## Skill Constitution
The permanent Skill principles of AegisAI:
1. **Dumb Actuators**: Skills contain zero governance logic. They are simply tools waiting for authorized input.
2. **Execution is a Privilege**: A Skill cannot run itself. It must be commanded by an Agent, authorized by a Human, and validated by Guardian.
3. **Absolute Portability**: Skills are decoupled, versioned, and immutable, guaranteeing that a workflow that works today will work exactly the same tomorrow.
