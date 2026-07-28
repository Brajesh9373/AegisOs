# AegisAI Plugin & SDK Architecture Specification

This document defines the definitive, permanent Plugin & SDK Architecture for AegisAI. It establishes the rules, sandboxing models, and governance frameworks for extending the platform through first-party and third-party code.

## 1. Plugin Philosophy
Extensibility is the lifeblood of a universal AI OS. However, third-party code is inherently untrusted. The Plugin Architecture must allow developers to deeply integrate new capabilities, data sources, and custom LLM providers into AegisAI without ever compromising the core platform's stability, data isolation, or Guardian governance.

## 2. SDK Philosophy
The Software Development Kit (SDK) must provide a sterile, strongly-typed, and backward-compatible interface. It acts as an API gateway for Plugins, ensuring that external code interacts with the AegisAI core only through strictly regulated, auditable pathways.

## 3. Objectives
The Plugin Architecture must:
* Provide a secure extension mechanism that does not require modifying the core AegisAI codebase.
* Enforce absolute sandboxing for all third-party code execution.
* Ensure all Plugin actions are evaluated by Guardian and logged in the Audit ledger.
* Support seamless distribution and version management via an internal Registry/Marketplace.

## 4. Plugin Architecture
A Plugin is a packaged executable bundle (e.g., WebAssembly module or isolated Docker container) containing a manifest, logic, and dependency definitions. Plugins do not run within the main AegisAI API process. They are invoked asynchronously over gRPC or isolated process boundaries.

## 5. Extension Architecture
Plugins augment the platform via predefined Extension Points. They cannot arbitrarily modify core logic; they can only attach to specific hooks exposed by the SDK.

## 6. Extension Points
* **Skill Plugins**: New tools (e.g., "SAP ERP Connector") that Agents can use.
* **Provider Plugins**: Custom LLM integrations (e.g., a proprietary internal model).
* **Knowledge Plugins**: Custom vectorization or OCR pipelines for unique file types.
* **UI Plugins**: Custom dashboard widgets or reporting formats.
* **Event Hook Plugins**: Custom logic triggered by Event Bus messages (e.g., a custom webhook dispatcher).

## 7. SDK Components
The SDK provides TypeScript/Python libraries that wrap the gRPC interfaces. It handles token injection, manifest generation, and standardized error mapping.

## 8. Plugin Lifecycle
1. **Development**: Built using the SDK.
2. **Packaging**: Bundled into a standardized archive.
3. **Registration**: Uploaded to the Plugin Registry.
4. **Validation**: Automated static analysis and security scanning.
5. **Approval**: Tenant Admin or Platform Admin enables the Plugin.
6. **Execution**: Triggered by Runtime or Event Bus in a secure sandbox.
7. **Deprecation**: Marked as obsolete, preventing new installations.

## 9. Plugin Registry
A centralized, versioned artifact repository storing all Plugin bundles available to the Organization. 

## 10. Plugin Versioning
Plugins follow Semantic Versioning (SemVer). The core platform enforces compatibility checks based on the manifest's declared required AegisAI version.

## 11. Plugin Compatibility
If a Plugin's declared SDK version is older than the minimum supported version of the active AegisAI platform, the Plugin is safely disabled at boot to prevent systemic crashes.

## 12. Plugin Validation
Upon upload, the registry automatically unpacks the Plugin, scans for known CVEs in dependencies, and verifies that the requested permissions match the manifest.

## 13. Plugin Certification
For high-security environments, Plugins can be cryptographically signed by AegisAI or an internal Security team. Uncertified Plugins can be universally blocked via Organization Settings.

## 14. Plugin Sandboxing
Execution occurs in an ephemeral, resource-constrained sandbox (e.g., strict WebAssembly runtimes or Firecracker microVMs). The sandbox limits CPU, memory, and execution time to prevent Denial of Service.

## 15. Plugin Permissions
Plugins operate on a strict "Least Privilege" model. The manifest must explicitly request permissions (e.g., `ReadKnowledge`, `CallExternalAPI: github.com`). These are presented to the Administrator during installation.

## 16. Plugin Isolation
Network egress from the Plugin sandbox is blocked by default. If a Plugin requires internet access, it must explicitly route traffic through the AegisAI egress proxy, which logs all outbound requests.

## 17. Plugin Security
Plugins are completely prohibited from reading system environment variables, accessing the host filesystem, or interacting directly with the PostgreSQL database.

## 18. Plugin Monitoring
The sandbox tracks the performance of every Plugin execution. If a Plugin consistently exceeds memory limits or crashes, it is automatically quarantined, and an alert is dispatched.

## 19. Plugin Audit
Every action a Plugin takes through the SDK is logged to the Audit Ledger. The log associates the action with both the Plugin ID and the `correlation_id` of the User/Agent that triggered it.

## 20. Distribution
Plugins can be distributed internally via the private Organization Registry, allowing Enterprise developer teams to build proprietary integrations.

## 21. Marketplace
A future public hub where verified third-party vendors can publish certified Plugins to the broader AegisAI ecosystem.

## 22. Updates
Plugin updates are applied seamlessly. Running tasks complete using the previous version; new tasks utilize the updated version.

## 23. Rollback
Because Plugins are immutable versioned artifacts, an Administrator can instantly roll back a failing Plugin to the previous version via the UI.

## 24. Future Expansion
The architecture fully embraces the Model Context Protocol (MCP), allowing standard MCP Servers to be registered dynamically as generic Plugins, instantly exposing their resources and tools to AegisAI.

## 25. Permanent Constraints
* Plugins never bypass Guardian.
* Plugins never access the database directly; they must use the SDK.
* Plugins always run in isolated, resource-constrained sandboxes.
* Plugins must respect Organization permissions and RBAC.
* All Plugin actions are perpetually auditable.

---

## Never Do

* **Never** execute Plugin code in the same memory space as the core AegisAI API.
* **Never** grant a Plugin root filesystem access or unfiltered host network access.
* **Never** allow a Plugin to bypass the `correlation_id` chain. If a Plugin executes a sub-task, it must pass the context forward.
* **Never** let a Plugin mutate core system configuration or alter Guardian policies.
* **Never** trust the Plugin manifest blindly; the sandbox must physically enforce the permissions declared in the manifest.

---

## Plugin Constitution
The permanent Plugin principles of AegisAI:
1. **The Principle of Mutual Distrust**: The core platform does not trust the Plugin, and the Plugin cannot harm the core platform. The sandbox is the absolute boundary.
2. **The Principle of Explicit Intent**: A Plugin cannot do anything it did not explicitly ask permission to do during installation. There are no hidden capabilities.
3. **The Principle of Regulated Extensibility**: AegisAI will grow infinitely through extensions, but it will never compromise its foundational governance to accommodate a third party.
