# AegisAI Platform Settings Architecture Specification

This document defines the definitive, permanent Settings Architecture for AegisAI. It establishes the configuration hierarchy, inheritance models, override rules, and governance for all tunable platform behaviors.

## 1. Settings Philosophy
Configuration is the steering wheel of the platform. In an enterprise environment, settings are not merely preferences; they are operational laws. The architecture must balance flexibility for end-users with absolute, unyielding control for global administrators. Configuration must be predictable, inherited cleanly, and strictly audited.

## 2. Objectives
The Settings Architecture must:
* Provide a unified, hierarchical configuration model from Platform down to the User.
* Enforce strict inheritance and override rules that prioritize security over convenience.
* Guarantee that every configuration change is versioned and easily reversible.
* Ensure that no user can unilaterally alter a dangerous setting without Guardian approval.

## 3. Settings Architecture
Settings are stored in a centralized configuration datastore, structured as typed JSON documents. Every setting is defined by a schema that dictates its data type, acceptable values, default value, and whether it can be overridden by lower hierarchical levels.

## 4. Platform Settings
Global configurations established by the infrastructure team or host. These apply across all tenants in a multi-tenant deployment. Examples: SMTP relay server, maximum global memory limit, global maintenance mode.

## 5. Organization Settings
Tenant-wide configurations. Examples: Custom branding, SSO SAML endpoints, default AI provider, global data retention policies.

## 6. Department Settings
Logical grouping configurations. Examples: Department token budget, default Workspace templates, default Guardian severity levels.

## 7. Workspace Settings
Project-specific configurations. Examples: Allowed external integrations, specific Agent prompt templates, Task timeout limits.

## 8. User Settings
Individual preferences. Examples: Dark mode, UI language, email notification preferences, default landing page.

## 9. Agent Settings
Persona configurations. Examples: Temperature (LLM creativity), default fallback model, maximum tools per execution.

## 10. Runtime Settings
Execution boundaries. Examples: Global context window hard limits, maximum retries for LLM inferences, streaming chunk size.

## 11. Guardian Settings
Policy definitions and enforcement rules. Examples: Blocked keyword lists, mandatory approval routing paths, risk threshold weights.

## 12. Notification Settings
Routing rules for alerts. Examples: Digest frequency, critical alert override channels (e.g., forcing PagerDuty for security events).

## 13. Security Settings
Access controls. Examples: Session timeout duration, MFA requirements, IP whitelist ranges.

## 14. License Settings
Entitlement tracking. Examples: Configured seat limits, active feature flags, expiration warnings.

## 15. AI Provider Settings
Upstream vendor configs. Examples: API keys (encrypted), base URLs, custom headers (e.g., ZDR tags).

## 16. Integration Settings
External system configs. Examples: Jira instance URL, GitHub Webhook secrets, Sync intervals.

## 17. Feature Flags
Boolean toggles used to safely roll out new platform features or disable broken components without requiring a full redeployment.

## 18. Configuration Inheritance
The hierarchy flows top-down: Platform → Organization → Department → Workspace → User. A setting evaluates by resolving the lowest specific value. If a User hasn't set a language, it falls back to the Workspace, then Department, etc.

## 19. Default Values
Every setting must have a hardcoded, secure-by-default value in the core application logic to ensure the platform boots even if the settings datastore is wiped.

## 20. Override Rules
A higher tier can "lock" a setting. If an Organization locks `MFA_Required = true`, no Department, Workspace, or User can override it to `false`.

## 21. Validation
Every setting change passes through a strict JSON schema validator. An administrator cannot accidentally set `SessionTimeout` to a string or a negative integer.

## 22. Versioning
Every settings document is versioned (e.g., `v1`, `v2`). Mutating a setting creates a new version, preserving the old one.

## 23. Backup
The complete configuration state is snapshotted nightly. 

## 24. Restore
Because settings are versioned JSON documents, restoring to a previous known-good state is instant and atomic.

## 25. Import
Administrators can import bulk configurations via JSON/YAML files, enabling Infrastructure-as-Code (IaC) parity.

## 26. Export
The entire hierarchical configuration state can be exported as a sanitized JSON payload (scrubbed of secrets) for compliance reporting or environment cloning.

## 27. Audit
Every single mutation of any setting at any level is permanently logged to the Audit Ledger, capturing the `before` and `after` diffs.

## 28. Monitoring
The system monitors configuration changes for rapid drift. A sudden burst of Organization-level security downgrades triggers an immediate `SecurityAlert`.

## 29. Security
Configuration APIs are protected by strict RBAC. Reading settings requires `config:read`, while mutating requires `config:write`. Reading sensitive settings (like AI Provider keys) is mathematically prohibited.

## 30. Future Expansion
The architecture supports the future addition of declarative GitOps syncing, where an Organization's configuration is automatically pulled and applied from a designated GitHub repository.

## 31. Permanent Constraints
* Platform settings override everything.
* Organization settings override department settings.
* User settings never override security or governance policies.
* Settings changes are always versioned.
* Every settings change is permanently auditable.
* Dangerous settings require explicit Approval Engine routing.
* The system must always support instant rollback of settings.

---

## Never Do

* **Never** store secrets (API keys, passwords) in plaintext within the Settings datastore. They must be handled by the specialized Secrets Management module.
* **Never** allow a User to downgrade their own security posture (e.g., turning off MFA) if the Organization has locked the setting.
* **Never** mutate a setting without creating a new historical version and an Audit log.
* **Never** deploy a new feature flag whose default state is enabled; all new features must default to safe/off.
* **Never** write application code that crashes if a setting is missing. Always provide a safe, hardcoded fallback.

---

## Settings Constitution
The permanent Settings principles of AegisAI:
1. **The Law of Gravity**: Authority flows downward. A higher level can dictate to a lower level, but a lower level can never circumvent the rules of the level above it.
2. **The Law of Memory**: A configuration mistake can take down an enterprise. The system must always remember exactly what the settings were 5 minutes ago, and it must allow instant reversal.
3. **The Law of Defaults**: When in doubt, the platform defaults to silence, security, and safety. Convenience must be explicitly configured.
