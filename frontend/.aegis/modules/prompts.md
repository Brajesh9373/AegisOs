# AegisAI Prompt Management Architecture Specification

This document defines the definitive, permanent Prompt Management Architecture for AegisAI. It establishes the rules, inheritance hierarchies, and governance models for assembling the contextual payloads that guide LLM logic and reasoning.

## 1. Prompt Philosophy
Prompts are the behavioral source code of an AI Agent. In an enterprise environment, prompts must be managed with the same rigor as traditional software source code: versioned, tested, auditable, and subject to strict governance. A prompt is a suggestion of intent; it is never a substitute for cryptographic security policies.

## 2. Objectives
The Prompt Architecture must:
* Provide a unified, hierarchical templating engine for constructing LLM payloads.
* Guarantee that system-level guardrails cannot be overridden by user-level prompts.
* Support instant rollback and side-by-side A/B testing of prompt versions.
* Prevent Prompt Injection attacks from escalating beyond the AI's sandboxed permissions.

## 3. Prompt Architecture
AegisAI employs a "Compositional Prompt Architecture." The final payload sent to the LLM is never a single string. It is dynamically assembled at runtime by the Prompt Engine, concatenating System Prompts, Organizational Guardrails, Agent Personas, and dynamic Task variables into a structured matrix (e.g., standard `System` / `User` / `Assistant` message arrays).

## 4. System Prompts
Hardcoded, immutable instructions embedded deep in the AegisAI core. These define the absolute baseline behavior (e.g., "You are an AI operating within AegisAI. You must format all tool calls as JSON.").

## 5. Organization Prompts
Tenant-wide instructions appended to every Agent in the organization. Example: "Never reference competitors by name. Always maintain a formal, corporate tone."

## 6. Department Prompts
Instructions scoped to a logical group. Example: "For all financial operations, explicitly state that your output is an estimate and not financial advice."

## 7. Team Prompts
Instructions bound to a specific working group. Example: "Always format code output using standard Python PEP-8 guidelines."

## 8. Agent Prompts
The specific persona and behavioral instructions for a distinct AI worker. Example: "You are SupportBot. Your primary goal is to resolve customer IT tickets quickly."

## 9. Task Prompts
The dynamic, ephemeral instructions provided by a human or trigger for a specific unit of work. Example: "Summarize this attached PDF."

## 10. Prompt Templates
Reusable, versioned strings containing dynamic variables (e.g., "Summarize the ticket `{{ticket_id}}` created by `{{user_name}}`").

## 11. Prompt Variables
Strictly typed data injected into templates at runtime. Variables are heavily sanitized to prevent injection attacks.

## 12. Prompt Composition
The Engine assembles the final prompt in a strict order:
1. System Prompts (Cannot be overridden)
2. Organization Prompts
3. Department Prompts
4. Agent Prompts
5. Task Prompts (User input)
6. Context (RAG data, Memory)

## 13. Prompt Versioning
Every modification to an Agent or Organization prompt creates a new immutable version (e.g., `v1.2.0`). In-flight tasks always execute against the prompt version active when the task was queued.

## 14. Prompt Testing
Before deployment, a prompt must be run through a "Playground" sandbox to test its reasoning against synthetic inputs and edge cases.

## 15. Prompt Validation
The Engine evaluates the final assembled prompt size against the configured LLM's context window limits. If the prompt exceeds the limit, it deterministically truncates older memory/context, never the System Prompts.

## 16. Prompt Approval
Modifying an Organization or Department prompt may trigger a Guardian policy requiring human-in-the-loop (HITL) approval before the new version becomes active.

## 17. Prompt Optimization
The platform supports tracking which prompt versions result in higher task success rates (e.g., fewer tool errors), enabling data-driven optimization.

## 18. Prompt Security
All User input (Task Prompts) is treated as hostile. It is conceptually isolated from System Prompts. While LLMs are susceptible to prompt injection, AegisAI relies on Guardian (Policy Engine) to ensure that even if the prompt is hijacked, the Agent's actual capabilities remain strictly bound by RBAC.

## 19. Prompt Monitoring
The size, cost, and generation latency associated with specific prompt templates are continuously tracked and surfaced in the Runtime Dashboard.

## 20. Prompt Audit
Every change to a prompt is logged in the Audit Ledger. The exact, fully assembled prompt sent to the external AI Provider is also logged in the Runtime Audit (scrubbed of PII if required by policy).

## 21. Prompt Rollback
If a new prompt version causes hallucinations or task failures, administrators can instantly revert the Agent to the previous version via the UI.

## 22. Prompt Inheritance
Similar to Settings, prompts inherit top-down. An Agent inherits the Organization's tone and guardrails automatically.

## 23. Prompt Overrides
A lower-level prompt (e.g., Agent Prompt) cannot instruct the LLM to ignore a higher-level prompt (e.g., System Prompt). If a conflict occurs, the LLM's behavior is unpredictable, but Guardian's enforcement remains absolute.

## 24. Future Expansion
The architecture supports the future addition of "Auto-Prompting," where a meta-LLM continuously refines an Agent's prompt based on historical task failure logs to improve reliability.

## 25. Permanent Constraints
* Prompts never override Guardian policies.
* Prompts never override RBAC permissions.
* Prompts are rigorously versioned.
* Prompts must be testable before deployment.
* Prompt mutations are permanently auditable.
* Instant rollback of prompt versions must be supported.
* The composition order (System first, User last) is immutable.

---

## Never Do

* **Never** store sensitive data (API keys, passwords, database credentials) directly inside a Prompt string. Use secure variable injection via the Integration layer.
* **Never** rely on a prompt instruction (e.g., "Do not delete the database") as a security mechanism. Security is enforced by Guardian; the prompt is merely a suggestion.
* **Never** mutate a prompt in place without creating a new historical version.
* **Never** allow User Input to be injected into the `System` role message array; User Input must always remain in the `User` role to minimize injection risks.

---

## Prompt Constitution
The permanent Prompt principles of AegisAI:
1. **The Principle of Suggestion**: A prompt is advice given to an AI. It is not code. It is not law. It is inherently probabilistic and cannot be trusted to enforce security boundaries.
2. **The Principle of Strict Hierarchy**: The system speaks first, the organization speaks second, the user speaks last. The core identity of the platform cannot be shouted down by a malicious user prompt.
3. **The Principle of Traceable Evolution**: As prompts are refined to improve AI behavior, the complete history of those changes must be perfectly preserved. We must always know exactly what we told the AI to do at any point in history.
