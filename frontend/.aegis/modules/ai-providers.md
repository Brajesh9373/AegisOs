# AegisAI AI Provider Architecture Specification

This document defines the definitive, permanent AI Provider Architecture for AegisAI. It establishes the rules, abstraction layers, and governance required to integrate with external and internal Large Language Model (LLM) providers.

## 1. Provider Philosophy
AegisAI is model-agnostic. The intelligence layer is a commoditized utility, completely decoupled from the platform's core governance, logic, and memory. An AI Provider is a swappable engine. Business logic must never be tightly coupled to the idiosyncrasies of a specific model or vendor.

## 2. Objectives
The AI Provider Architecture must:
* Provide a unified interface for interacting with any LLM provider.
* Support seamless fallback and failover across multiple providers.
* Ensure secret keys and organizational data are rigorously protected.
* Normalize capabilities (like Tool Calling and Vision) across divergent vendor APIs.

## 3. Provider Architecture
The Provider layer sits directly beneath the Runtime. When the Runtime requires an inference, it queries the Provider Registry, selects the active Model, formats the prompt into a standardized internal representation, and passes it to the Provider Adapter. The Adapter translates the standard payload into the vendor-specific API schema, executes the request, and normalizes the response back to the Runtime.

## 4. Provider Registry
A central database of configured providers for the tenant. It stores the provider identifier, API base URLs (useful for proxies), and references to securely stored API keys.

## 5. Provider Abstraction
All interactions with models occur through standard interfaces (e.g., `generate_text`, `stream_response`, `execute_tool`). The Runtime never imports vendor SDKs directly; it only invokes the internal Adapter.

## 6. Model Registry
A catalog of available models (e.g., `gpt-4o`, `claude-3-opus`, `llama3-70b`) mapped to their parent Provider. The registry tracks the model's capabilities (context window size, tool calling support, multimodality).

## 7. Model Selection
Agents are configured with a primary model. When a Task executes, the Runtime binds the Agent to the specified model from the Registry. 

## 8. Provider Switching
Administrators can hot-swap the primary model for an Agent or the entire workspace without altering any Prompts or Skills. The abstraction layer handles the translation.

## 9. Failover
If the primary provider API returns a 5xx error or times out, the Runtime can automatically failover to a configured secondary model (e.g., if Anthropic goes down, route the inference to Azure OpenAI).

## 10. Load Distribution
For high-volume Enterprise deployments, inferences can be round-robined across multiple API keys or multiple regions of the same provider to avoid hitting rate limits.

## 11. Cost Tracking
The Adapter calculates token usage (input and output) for every request. This is logged to the Audit ledger and associated with the specific Task, Agent, and Organization, enabling granular chargebacks.

## 12. Health Monitoring
Background workers continuously ping configured providers to assess API latency and uptime, disabling unhealthy providers from the routing pool dynamically.

## 13. Provider Authentication
Authentication varies by provider (Bearer tokens, API keys, IAM roles). The Adapter handles the specific authentication handshake required by the vendor API.

## 14. Secret Management
API keys are never stored in plaintext. They are encrypted at rest using the tenant's KMS key and decrypted in memory only at the exact moment the HTTP request is assembled.

## 15. Rate Limits
The architecture respects vendor rate limits (HTTP 429) by implementing token bucket throttling locally, preventing the system from being temporarily banned by the upstream provider.

## 16. Retry Strategy
Transient failures (e.g., HTTP 503) trigger an exponential backoff retry loop within the Adapter, shielding the Task Engine from temporary network blips.

## 17. Timeouts
Strict timeouts are enforced. If an LLM hangs during generation, the connection is forcefully severed after the TTL, and the failure is logged.

## 18. Streaming
The Provider architecture fully supports Server-Sent Events (SSE). The Adapter streams normalized tokens back to the Runtime, allowing real-time UI updates in chat interfaces.

## 19. Capability Discovery
Models are tagged with capabilities (e.g., `supports_tools: true`, `supports_vision: false`). If a Task requires a Skill (tool), the Runtime prevents assignment to a model lacking tool support.

## 20. Compatibility
The Adapter must gracefully downgrade where possible. If a prompt contains an image, but the fallback model does not support Vision, the Adapter strips the image and appends a warning to the text, rather than crashing.

## 21. Provider Versioning
APIs evolve. The Provider Registry allows administrators to pin specific API versions (e.g., OpenAI `2024-02-15-preview`) to guarantee stability.

## 22. Provider Security
Zero-Data Retention (ZDR) headers are automatically injected into requests where supported, explicitly instructing the vendor not to log or train on the tenant's prompt data.

## 23. Future Expansion
The architecture supports the addition of custom, fine-tuned models hosted on proprietary infrastructure.

## Supported Providers
The architecture officially supports adapters for:
* **OpenAI**
* **Anthropic**
* **Google** (Gemini)
* **Azure OpenAI** (Enterprise-grade endpoints)
* **Ollama** (Local, offline inference)
* **OpenRouter** (Unified API aggregator)
* **Future Providers** (Extensible via the Adapter pattern)

## 24. Permanent Constraints
* Runtime communicates exclusively with Providers.
* Providers never bypass Runtime.
* Providers never bypass Guardian.
* Providers are infinitely replaceable.
* Providers are completely configurable.
* Core business logic never depends on a specific provider.

---

## Never Do

* **Never** hardcode model-specific formatting (e.g., Claude's specific XML tag preferences) into the core database or application logic; all formatting happens in the Adapter.
* **Never** expose an API Key in the UI after it is saved.
* **Never** allow a Provider to execute a tool. The Provider *requests* a tool; the Runtime and Guardian *execute* it.
* **Never** transmit sensitive prompts to a Provider unless the Organization has explicitly opted in and accepted the data processing agreement for that vendor.
* **Never** use a Provider's proprietary features (e.g., OpenAI Assistants API state management) to store AegisAI state. All state, memory, and task tracking lives inside AegisAI databases.

---

## AI Provider Constitution
The permanent AI Provider principles of AegisAI:
1. **The Intelligence Commodity**: Models are temporary; governance is permanent. Do not attach the platform's survival to a single vendor.
2. **The Dumb Pipe**: The Provider API is a dumb pipe. It takes text in, and it gives text out. It has zero authority to mutate system state.
3. **Data Sovereignty**: We treat external APIs as hostile environments. Data only leaves the perimeter when explicitly requested by a governed Task, and only to vendors approved by the enterprise.
