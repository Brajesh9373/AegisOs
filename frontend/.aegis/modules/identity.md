# AegisAI Identity & Authentication Architecture Specification

This document defines the definitive, permanent Identity & Authentication Architecture for AegisAI. It establishes how human and machine actors prove who they are, how sessions are managed, and how identity forms the unbreakable foundation for all subsequent authorization and governance.

## 1. Identity Philosophy
Identity is the anchor of accountability. In an Enterprise AI OS, every single action—whether initiated by a CEO, an API script, or an autonomous AI Agent—must trace back to a mathematically proven, singular identity. Without absolute certainty of *who* is acting, RBAC and Guardian policies are useless.

## 2. Identity Architecture
The Identity Provider (IdP) module serves as the front door. It handles the cryptographic verification of credentials, manages session states (JWTs/Cookies), and issues the universally unique `subject_id` that is attached to every downstream request, database mutation, and Audit Ledger entry.

## 3. Authentication
Authentication (proving who you are) is strictly decoupled from Authorization (proving what you can do). Authentication occurs exactly once per session. The resulting token is then continuously evaluated by the RBAC and Guardian modules for Authorization.

## 4. Authorization Integration
The Identity module passes the authenticated `subject_id` and `tenant_id` claims to the API gateway. The API gateway immediately hydrates the user's RBAC roles from the database and attaches them to the request context before hitting any business logic.

## 5. Identity Providers
AegisAI supports a federated identity model. While it includes a localized identity database, enterprise deployments strictly utilize external Identity Providers (IdP) to maintain a single source of corporate truth.

## 6. Local Authentication
Used primarily for initial bootstrap (the "Root" admin account) or isolated edge deployments. Utilizes Argon2id for password hashing.

## 7. LDAP / Active Directory
Supported for legacy enterprise synchronization. The system binds to the LDAP server to verify credentials and optionally syncs groups to AegisAI Teams.

## 8. OAuth / OIDC
The primary modern authentication mechanism. Supports Google Workspace, Microsoft Entra ID (Azure AD), and generic OpenID Connect providers.

## 9. SAML
Supported for enterprise Single Sign-On (SSO). AegisAI acts as the Service Provider (SP), consuming assertions from the Identity Provider (IdP) (e.g., Okta, PingIdentity).

## 10. MFA (Multi-Factor Authentication)
MFA is natively supported via TOTP (Time-based One-Time Password) and WebAuthn/FIDO2 (Hardware Keys). MFA can be enforced globally by Organization Policy or conditionally by Guardian based on risk.

## 11. Password Policies
If Local Authentication is used, the engine enforces strict, configurable complexity rules, history checks, and dictionary attack prevention.

## 12. Session Management
Sessions are managed via stateless JWTs (JSON Web Tokens) for API speed, backed by a stateful Redis cache to allow instant, global session revocation.

## 13. API Authentication
External systems interacting with AegisAI APIs authenticate using long-lived, cryptographically secure Bearer Tokens (API Keys).

## 14. Service Accounts
Non-human accounts used for CI/CD pipelines or background integrations. They are bound by the same RBAC and Guardian rules as human accounts but cannot access the UI.

## 15. Agent Identity
Every AI Agent has a unique, cryptographic identity. When an Agent executes a Task, its `agent_id` is the primary actor in the Audit log, explicitly linked to the `owner_id` of the human who spawned it.

## 16. Machine Identity
Internal microservices (e.g., Task Engine, Reporting Engine) authenticate with each other using mTLS (Mutual TLS) and internal short-lived JWTs.

## 17. Token Lifecycle
Access Tokens (JWTs) are short-lived (e.g., 15 minutes). Refresh Tokens are long-lived (e.g., 7 days) and are stored securely in HTTP-only, secure cookies.

## 18. Token Rotation
Refresh tokens are rotated upon every use. If a stolen refresh token is reused, the system detects the anomaly and instantly revokes all active sessions for that user.

## 19. Account Recovery
Automated password resets via email (for Local Auth) or deferred entirely to the external IdP (for SSO).

## 20. Account Lockout
After N failed authentication attempts, the account is temporarily locked to prevent brute-force attacks. Lockout events trigger Security Alerts.

## 21. Account Lifecycle
Provisioned → Active → Suspended → Soft-Deleted. Accounts are never hard-deleted to preserve the integrity of historical Audit logs.

## 22. Identity Monitoring
The system monitors login velocity (e.g., impossible travel alerts), brute-force attempts, and sudden spikes in API Key usage.

## 23. Identity Audit
Every successful login, failed login attempt, password change, MFA enrollment, and token revocation is permanently recorded in the Audit Ledger.

## 24. Future Expansion
The architecture supports the future addition of Continuous Authentication, where behavioral biometrics (typing cadence, mouse movement) continuously validate the user's identity during the session.

## 25. Permanent Constraints
* Every actor (Human, Agent, System) has exactly one unique identity.
* Authentication strictly precedes Authorization.
* MFA must be natively supported and enforceable.
* Sessions must be globally and instantly revocable.
* Identity context must never be bypassed by Guardian.

---

## Never Do

* **Never** store passwords in plaintext, or using weak hashes (MD5, SHA1). Always use Argon2id or bcrypt.
* **Never** log sensitive authentication payloads (passwords, JWTs, Session Cookies) to application logs or the Audit Ledger.
* **Never** trust a JWT signature without verifying it against the authoritative public key.
* **Never** build a "backdoor" identity or hardcoded admin credentials bypassing the IdP routing.
* **Never** allow an API Key to have global, unlimited permissions; they must be scoped.

---

## Identity Constitution
The permanent Identity principles of AegisAI:
1. **The Principle of Singularity**: One Actor, One Identity. There are no shared accounts, no anonymous actions, and no ghosts in the machine.
2. **The Principle of Impermanence**: Trust degrades over time. Sessions expire. Tokens rotate. Re-authentication is a feature, not a bug.
3. **The Principle of Delegation**: When an AI Agent acts, it acts on behalf of a Human. The Agent has an identity, but the Human holds the ultimate accountability.
