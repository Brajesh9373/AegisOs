# AegisAI Model Context Architecture Specification

This document defines the definitive, permanent AI Model Context Architecture for AegisAI. It establishes the rules, assembly algorithms, and security boundaries for injecting deterministic enterprise data into the non-deterministic LLM context window.

## 1. Context Philosophy
An LLM is a stateless reasoning engine; it only knows what it is told in the current prompt. Context is the bridge between the AI's generic intelligence and the Enterprise's specific reality. Because context dictates behavior, the assembly of context is a highly governed, strictly permissioned, deterministic engineering process.

## 2. Context Objectives
The Context Architecture must:
* Dynamically assemble the perfect subset of enterprise data required for a specific task.
* Mathematically guarantee that no unauthorized data enters the context window.
* Optimize token consumption by prioritizing the most relevant data.
* Ensure the context assembly process is fully traceable and explainable.

## 3. Context Sources
Context is federated from multiple data silos: Vector Databases (Knowledge/Memory), Relational Databases (Configuration/Policy), and real-time APIs (Tools/Skills). The Context Engine acts as the aggregator.

## 4. Organization Context
Global guardrails and facts. Example: "You are representing ACME Corp. The CEO is Jane Doe." This is injected into the `System` prompt array for all Agents in the tenant.

## 5. Department Context
Domain-specific operating procedures. Example: "In the Finance Department, all monetary values must be formatted in USD."

## 6. User Context
Information about the human initiating the task. Example: "The user requesting this summary is John Smith, a Level 2 Support Engineer."

## 7. Agent Context
The core persona definition. Example: "You are SupportBot. Your primary directive is resolving tickets using the Zendesk integration."

## 8. Task Context
The ephemeral parameters of the current execution. Example: "The current ticket ID is #9942, and the subject is 'Cannot login'."

## 9. Knowledge Context
Data retrieved via RAG (Retrieval-Augmented Generation). The Context Engine queries the Vector DB based on the Task prompt and injects the top K most relevant document chunks.

## 10. Memory Context
Data retrieved from the Agent's episodic history. Example: "In a previous step, you tried the `ResetPassword` tool and it failed with a 403 error."

## 11. Skill Context
The JSON Schemas of the tools the Agent is currently permitted to use, informing the LLM of its available capabilities.

## 12. Policy Context
Explicit rules injected to guide the LLM's reasoning before Guardian physically enforces them. Example: "Do not attempt to delete databases; you do not have permission."

## 13. Approval Context
When a task resumes after human approval, the context is injected. Example: "The human manager 'Alice' approved the budget increase with the comment: 'Proceed cautiously'."

## 14. Context Prioritization
Because context windows are finite, data is prioritized when limits are approached:
1. System/Organization Policies (Highest)
2. Agent Persona
3. Task Prompt
4. Skill Schemas
5. Knowledge RAG
6. Historical Memory (Lowest, truncated first)

## 15. Context Limits
The Context Engine respects a hard token limit (e.g., 128k tokens). If the assembled payload exceeds the limit, the Engine applies deterministic truncation based on the Prioritization rules.

## 16. Context Optimization
The Engine employs caching and summarization. If historical memory exceeds 10k tokens, a background worker uses a smaller, cheaper LLM to summarize it into a 500-token block before injecting it into the active context.

## 17. Context Validation
Before the final payload is transmitted to the AI Provider, the Engine scans the context block for missing variables or malformed JSON, failing fast if the context is corrupt.

## 18. Context Security
The absolute boundary. When the Context Engine queries the Vector DB for Knowledge Context, it explicitly binds the query to the User's RBAC scope. If the LLM asks to summarize "Project X," but the User lacks access to "Project X," the Context Engine returns an empty array. The LLM cannot hallucinate access to data it was never given.

## 19. Future Expansion
The architecture supports the integration of "Graph-Based Context," where the Engine traverses an Enterprise Knowledge Graph to pull deeply connected entities (e.g., pulling a User, their Manager, and their active Projects) into context simultaneously.

## 20. Permanent Constraints
* Context assembly must be explicitly permission-aware.
* Context generation can never bypass RBAC constraints.
* The truncation and prioritization algorithms must be deterministic.
* The final context payload sent to the LLM must be fully logged and explainable.

---

## Never Do

* **Never** inject the entire database or raw, unfiltered search results into the context window; always use Semantic Search (RAG) to find the specific, relevant chunks.
* **Never** query context data using a "system administrator" token; always query the underlying databases using the strict RBAC identity of the User initiating the task.
* **Never** allow User Input (Task Context) to overwrite or disable the Organization Context (System Prompts).
* **Never** fail silently if the context window is exceeded; apply deterministic truncation and log a `WARN` event, or fail the task if critical context cannot fit.

---

## Model Context Constitution
The permanent Context principles of AegisAI:
1. **The Principle of the Sterile Room**: The LLM is a blank slate. It knows absolutely nothing about the enterprise until the Context Engine hands it a dossier. The security of the AI is entirely dependent on the security of that dossier.
2. **The Principle of Filtered Reality**: An Agent's worldview is strictly bounded by the RBAC permissions of its human owner. If the owner cannot see a file, the file does not exist in the Agent's universe.
3. **The Principle of Strict Hierarchy**: In the war for tokens, Policy always defeats Memory. When space runs out, the Agent forgets the past, but it never forgets the rules.
