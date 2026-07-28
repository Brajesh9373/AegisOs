# AegisAI License Architecture Specification

This document defines the definitive, permanent License Architecture for AegisAI. It establishes the rules, lifecycle, governance, and mechanics for how entitlements, limits, and features are provisioned and verified across self-hosted deployments.

## 1. License Philosophy
AegisAI is a self-hosted platform. The customer owns the infrastructure, the data, and the AI provider costs. The licensing model is exclusively feature-based and capacity-based, never token-based. A license governs *access* to platform capabilities, but it never assumes ownership or control over the customer's business data.

## 2. Objectives
The License Architecture must:
* Securely enforce feature entitlements and capacity limits.
* Support completely air-gapped, offline deployments.
* Prevent circumvention of platform limits without degrading runtime performance.
* Ensure expired licenses never destroy or hold hostage organizational data.
* Maintain a transparent, auditable lifecycle for activation and renewal.

## 3. Licensing Architecture
The Licensing Engine is a standalone validation module within the platform. It intercepts critical application initialization and periodic health checks to verify the active license signature. It maps the cryptographically signed license payload to internal Feature Flags.

## 4. Self Hosted Licensing Model
Since the customer hosts the platform, AegisAI cannot rely on continuous SaaS validation. The license is a cryptographically signed digital document (e.g., a JWT or signed JSON payload) delivered to the customer and injected into their environment.

## 5. Online License Activation
The instance securely connects to the AegisAI license server to fetch, validate, and install the license payload automatically based on a customer activation key.

## 6. Offline License Activation
The customer downloads a physical license file from a secure portal and manually uploads it to their air-gapped AegisAI instance. 

## 7. License Validation
The process of cryptographically verifying that the license payload has not been tampered with, was issued by the AegisAI authority, and has not expired.

## 8. License Verification
The process of ensuring the validated license matches the current environment (e.g., matching the Hardware Fingerprint).

## 9. License Renewal
A seamless process where a new license payload extends the expiration date. The platform transparently hot-swaps the active license without requiring a restart.

## 10. License Expiration
When a license expires, the platform transitions to a degraded state. Mutative operations (e.g., creating new agents, assigning new tasks) are disabled. 

## 11. Grace Period
A configurable window (e.g., 14 days) following expiration where the platform continues full operation, emitting critical warnings to administrators, before entering the degraded state.

## 12. Trial License
A fully-featured, strictly time-bound license used for evaluation.

## 13. Community License
A free, perpetual license with hardcoded limits (e.g., 1 Workspace, 5 Agents).

## 14. Commercial License
A paid license unlocking standard enterprise features and increasing limits.

## 15. Enterprise License
The highest tier, unlocking unlimited scale, advanced SSO, White Labeling, and premium integrations.

## 16. White Label License
An entitlement that permits the removal of AegisAI branding, allowing the enterprise to fully customize the UI for internal branding.

## 17. License Features
Specific platform capabilities tied to entitlements (e.g., "Advanced Audit Export", "Custom Skill Imports").

## 18. Feature Flags
Internal boolean toggles mapped directly to License Features. If the license lacks the feature, the flag evaluates to `false`, hiding the UI and blocking the API.

## 19. Module Licensing
Certain advanced domains (e.g., "Advanced Analytics Module") can be licensed independently as add-ons to a base license.

## 20. User Limits
Maximum number of active human users (Seats) permitted.

## 21. Agent Limits
Maximum number of active AI Agents permitted across the instance.

## 22. Organization Limits
Maximum number of top-level tenant Organizations in a multi-tenant deployment.

## 23. Department Limits
Maximum number of departments allowed within an Organization.

## 24. Workspace Limits
Maximum number of isolated Workspaces.

## 25. AI Provider Limits
Restrictions on which LLM providers (e.g., OpenAI, Anthropic, Local OS Models) can be configured.

## 26. Storage Limits
Platform-enforced soft limits on Knowledge Document storage (though physical storage is bounded only by customer infrastructure).

## 27. Memory Limits
Restrictions on the retention window or volume of Agent Memory.

## 28. Skill Limits
Maximum number of Custom or External Skills that can be imported.

## 29. Knowledge Limits
Maximum number of certified Knowledge assets.

## 30. API Limits
Rate limits on the external SDK/API (managed locally to prevent abuse of the platform).

## 31. Branding Options
Entitlements allowing custom logos, color themes, and domain masking.

## 32. SSO Options
Entitlements unlocking SAML, OIDC, or Active Directory integrations.

## 33. Multi Organization Support
Entitlement allowing a single instance to host completely isolated tenant Organizations.

## 34. Multi Workspace Support
Entitlement allowing an Organization to host multiple isolated Workspaces.

## 35. License Transfer
Moving a license to a new physical server. Requires invalidating the old hardware fingerprint and issuing a new license payload via the customer portal.

## 36. Machine Binding
Tying a license to a specific physical or virtual machine to prevent the customer from spinning up unauthorized shadow instances.

## 37. Hardware Fingerprint
A hash generated from stable host hardware identifiers (e.g., MAC address, CPU ID) used during Machine Binding.

## 38. License Encryption
The license payload is encrypted and signed using asymmetric cryptography (e.g., RSA/ECC). The AegisAI platform contains the public key; only the AegisAI authority holds the private key.

## 39. License Security
The Licensing Engine is heavily obfuscated. Validation routines are scattered throughout core application logic to prevent a single-point bypass patch.

## 40. License Audit
Every activation, failure, expiration, and limit breach is logged to the immutable Audit ledger.

## 41. License Monitoring
The platform continuously monitors current usage against licensed limits, alerting administrators at 80%, 90%, and 100% capacity.

## 42. License Notifications
Automated alerts dispatched to Platform Administrators regarding impending expirations or limit saturation.

## 43. License Versioning
The structure of the license payload is versioned to support future platform capabilities without breaking older deployments.

## 44. Upgrade Strategy
Applying a higher-tier license instantly updates Feature Flags and unlocks limits without requiring a system restart.

## 45. Downgrade Strategy
Applying a lower-tier license gracefully disables premium features. If current usage exceeds the new lower limits, the system enters a read-only state for the excess entities until the admin manually reduces usage to comply.

## 46. Backward Compatibility
Newer versions of the AegisAI platform must always accept and parse older valid license formats.

## 47. Disaster Recovery
In a catastrophic failure, a "Cold Standby" backup server can be spun up using the same license, provided the Hardware Fingerprint is legally transferred or the license permits High Availability (HA) clustering.

## 48. Future Expansion
The license payload is extensible, utilizing an open JSON structure (signed) to allow arbitrary future feature toggles.

## 49. Permanent Constraints
* Licensing is feature-based, NOT token-based.
* Customer owns infrastructure and AI provider costs.
* License never controls or transmits business data.
* Expired license never deletes customer data.
* License validation must never impact Runtime performance.

---

## Conceptual Definitions

* **License**: The cryptographic document granting platform access.
* **Subscription**: The commercial agreement dictating the terms and duration of the License.
* **Activation**: The initial injection of the License into the platform.
* **Validation**: Checking the cryptographic integrity and expiration date.
* **Verification**: Ensuring the License matches the host machine.
* **Feature Flag**: Internal toggle mapped to a License entitlement.
* **Plan**: A marketing bundle (e.g., "Pro", "Enterprise") mapping to a set of limits.
* **Module**: An architectural domain (e.g., Task Engine) that can be individually licensed.
* **Workspace**: An isolated environment within an Organization.
* **Organization**: A top-level tenant.
* **Seat**: A licensed human user.
* **Agent**: A licensed AI persona.

---

## Deployment & Flow Examples

**Enterprise Deployment Example**: 
A global bank deploys AegisAI in an air-gapped Kubernetes cluster. They generate a Hardware Fingerprint from their cluster nodes, download the `license.key` from the AegisAI portal via a separate machine, and inject it into their Kubernetes Secrets. The Licensing Engine validates the key offline and unlocks the platform.

**Online Activation Flow**:
1. Admin enters 16-character Activation Key in the UI.
2. Platform calls `https://license.aegisai.com/api/v1/activate` sending the Key and Hardware Fingerprint.
3. Server verifies subscription and returns the signed License Payload.
4. Platform saves Payload to DB, updates Feature Flags, and unlocks UI.

**Offline Validation Flow**:
1. Platform boots up.
2. Reads License Payload from DB or File System.
3. Decrypts and verifies RSA signature.
4. Checks `ExpiresAt` > `CurrentDate`.
5. Checks `Fingerprint` == `LocalHardwareHash`.
6. Passes: Platform boots. Fails: Platform boots into "License Error" recovery UI.

**Upgrade Example**:
An organization on the "Community Plan" (5 Agents limit) purchases "Commercial". The admin pastes the new payload. The system immediately allows the creation of the 6th agent without dropping active connections.

**Expiration & Recovery Example**:
A license expires. After the 14-day Grace Period, the platform locks all "Create" buttons. Existing agents can still answer historical queries (Read-Only), but cannot execute new Tasks. The admin procures a new key, pastes it into the portal, and full functionality is instantly restored. No data is lost.

---

## Never Do

* **Never** charge per LLM token; AegisAI licenses the platform capability, not the AI consumption.
* **Never** phone home with customer business data, memory, or knowledge under the guise of "license telemetry".
* **Never** hard-delete users, agents, or data if a license expires or limits are exceeded.
* **Never** place synchronous license validation checks inside the high-frequency Runtime LLM loop (validate at startup or asynchronously).
* **Never** allow license verification to bypass Guardian security checks.
* **Never** implement a "kill switch" that actively destroys a customer deployment.
* **Never** rely on system time alone without sanity checks, to prevent expiration bypassing via clock rollbacks.

---

## License Constitution
The permanent Licensing principles of AegisAI:
1. **Sovereignty**: The customer owns their data and their infrastructure. The license governs the software, not the business.
2. **Transparency**: The platform must never hold customer data hostage. Expiration degrades capability, but data remains accessible for extraction.
3. **Resilience**: The licensing architecture must support total isolation. An enterprise must be able to run AegisAI forever on a valid perpetual license without ever connecting to the internet.
