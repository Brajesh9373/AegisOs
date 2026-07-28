# AegisAI AI Provider Routing Architecture Specification

This document defines the definitive, permanent AI Provider Routing Architecture for AegisAI. It establishes the intelligent gateway that intercepts AI requests, evaluates business rules, and routes the payload to the optimal upstream LLM provider.

## 1. Routing Philosophy
No single AI model is perfect for every task. Enterprise platforms must avoid vendor lock-in and optimize for cost, speed, and capability on a per-task basis. The Router is the economic and operational brain of the AI infrastructure. It abstracts the underlying providers (OpenAI, Anthropic, local OSS models) so the user and the internal Task Engine simply ask for "intelligence" and the Router figures out the best way to procure it.

## 2. Objectives
The Routing Architecture must:
* Decouple the core Task Engine from specific vendor APIs.
* Dynamically route requests based on cost, required capabilities, and current provider health.
* Automatically failover to backup models during upstream outages.
* Ensure all routing decisions are transparent and auditable.

## 3. Routing Architecture
The Router sits between the Context Builder (which finalized the payload) and the external network boundary. It evaluates the payload metadata against a hierarchical set of Routing Policies, selects the optimal target, translates the internal AegisAI payload into the specific vendor's API format, and executes the HTTP request.

## 4. Model Selection
If an Agent or Task specifically requests a model (e.g., `model: gpt-4o`), the Router respects that choice *unless* a Routing Policy overrides it. If no model is specified, the Router dynamically selects one based on the Capability Matching engine.

## 5. Capability Matching
The Router maintains a dynamic registry of available models and their capabilities (e.g., Vision, Function Calling, 128k Context Window). If a Task includes an image, the Router automatically filters out text-only models before making a selection.

## 6. Cost Optimization
The Router evaluates the token size of the incoming prompt. If the task is simple (e.g., "Summarize this paragraph") and the tokens are few, the Router may downgrade the request from an expensive flagship model to a faster, cheaper model (e.g., Claude 3 Haiku) based on Cost Policies.

## 7. Availability
The Router continuously monitors the real-time latency and HTTP error rates of all configured upstream providers.

## 8. Failover
If the primary selected model returns a 5xx error or times out, the Router immediately and transparently retries the request against the next best available model in the fallback chain.

## 9. Load Balancing
For self-hosted or provisioned-throughput models (e.g., Azure OpenAI PTU), the Router distributes requests across multiple regional endpoints to prevent localized throttling.

## 10. Routing Policies
Rules defined by the Organization or Department. Example: "All tasks containing PHI must be routed to the self-hosted Llama-3 cluster, regardless of Agent preference."

## 11. Routing Rules
The specific Boolean logic evaluated by the Router. Examples include matching by `tenant_id`, `task_type`, `estimated_cost`, or `data_classification_level`.

## 12. Provider Health
A background daemon continuously pings all configured providers with lightweight tests. If a provider's error rate exceeds a threshold, the daemon marks the provider as "Degraded" and the Router temporarily removes it from the active pool.

## 13. Provider Fallback
A statically defined chain of custody for reliability. Example: Try Azure OpenAI East US → Try Azure OpenAI West US → Try Anthropic AWS Bedrock.

## 14. Monitoring
The Router emits highly granular metrics for every request: `provider_latency_ms`, `tokens_consumed`, `routing_decision_reason`, and `failover_count`.

## 15. Audit
Every routing decision is logged in the `TaskExecution` record. If an external auditor asks why an Anthropic model processed a specific prompt instead of an OpenAI model, the exact policy that triggered the route is permanently recorded.

## 16. Future Expansion
The architecture supports the integration of "Semantic Routing," where a very fast, local classifier model reads the prompt and determines its complexity, routing simple greetings to cheap models and complex math to expensive models dynamically.

## 17. Permanent Constraints
* The Router must never bypass the Runtime or Guardian; it only executes what Guardian has already approved.
* Routing policies must support strict overrides based on data classification.
* Failover mechanisms must be transparent to the initiating Agent/User.
* Every routing decision must be permanently auditable.

---

## Never Do

* **Never** hardcode specific provider API endpoints directly into Agent logic or Task Engine workers; all network traffic must pass through the Router.
* **Never** allow a Cost Optimization downgrade to violate a Security Policy (e.g., routing to a cheaper public API when a private API is mandated).
* **Never** attempt infinite failover loops. The fallback chain must have a terminal end that returns a hard error to the user.
* **Never** store provider API keys within the Router codebase; they must be fetched from the Secrets Manager at runtime.

---

## Provider Routing Constitution
The permanent Routing principles of AegisAI:
1. **The Principle of Abstraction**: The enterprise does not buy models; it buys intelligence. The underlying provider is an implementation detail that can and will be swapped out at a moment's notice.
2. **The Principle of Economic Gravity**: Intelligence flows to the cheapest, fastest model capable of solving the problem. Flagship models are reserved for flagship problems.
3. **The Principle of Undeniable Pathing**: How a prompt reached a specific server is a critical security question. Every twist, turn, and failover in the routing path must be meticulously documented.
