# AegisAI Prompt Builder Architecture Specification

This document defines the definitive, permanent Prompt Builder Architecture for AegisAI. It establishes the hierarchical composition, templating, and injection mechanics used to construct the literal string instructions passed to an LLM.

## 1. Prompt Builder Philosophy
If the Context Builder manages *what* the AI knows (the data), the Prompt Builder manages *how* the AI thinks (the instructions). LLMs are highly susceptible to instruction drift and prompt injection. Therefore, prompt assembly cannot be ad-hoc string concatenation. It is a rigid, layered templating system that enforces enterprise governance at the syntactic level.

## 2. Objectives
The Prompt Builder Architecture must:
* Assemble complex instructions deterministically using a strict, un-bypassable hierarchy.
* Resolve dynamic variables securely without exposing the system to injection attacks.
* Version all prompt templates to allow instant rollback if AI performance degrades.
* Provide an immutable audit trail of the exact instruction set sent to the provider.

## 3. Prompt Assembly
The Prompt Builder is a sub-component of the Context Builder. It specifically handles the text block traditionally passed in the `role: system` array. It fetches versioned markdown/text templates from the database and compiles them into a single, cohesive directive.

## 4. Prompt Layers
Instructions are stacked from most authoritative to least authoritative. Lower layers can never contradict or overwrite the constraints defined by higher layers. The Prompt Builder physically prepends higher-layer text to ensure the LLM reads it first.

## 5. System Instructions
The absolute baseline (Layer 1). Hardcoded by the Platform. Example: "You are an AI assistant running on AegisAI. You must always return valid JSON. You must never invent functions."

## 6. Organization Instructions
Tenant-wide mandates (Layer 2). Example: "You represent OmniCorp. Always maintain a professional, corporate tone. Never discuss internal competitor analysis."

## 7. Department Instructions
Domain-specific mandates (Layer 3). Example: "As a Legal Department AI, you must explicitly state that your output is not formal legal advice."

## 8. Agent Instructions
The AI Persona definition (Layer 4). Example: "You are CodeReviewBot. Your job is to find security vulnerabilities in Python code."

## 9. Task Instructions
The ephemeral user directive (Layer 5). Example: "Review the attached file `auth.py` for SQL injection flaws."

## 10. Dynamic Variables
Templates contain typed variables (e.g., `{{user.name}}`, `{{current_time}}`, `{{workspace.id}}`). The Prompt Builder resolves these using a secure templating engine (e.g., Jinja2 or Handlebars). The engine explicitly HTML-escapes or sanitizes these variables to prevent secondary prompt injection.

## 11. Context Injection
The Prompt Builder leaves explicit anchor tags (e.g., `<KNOWLEDGE_CONTEXT>`) in the assembled prompt. The parent Context Builder later injects the RAG data into these exact slots.

## 12. Prompt Validation
Before compilation completes, the Builder checks the prompt against Guardian policies. It also ensures the prompt does not exceed a hardcoded "instruction budget" (e.g., System prompts cannot consume more than 20% of the total token window).

## 13. Prompt Optimization
The Builder strips unnecessary whitespace, comments, and redundant instructions to minimize token consumption before finalizing the string.

## 14. Prompt Versioning
Every modification to an Organization, Department, or Agent template creates a new immutable version. If `v4` causes the AI to hallucinate, an Admin can instantly revert the routing table to use `v3`.

## 15. Prompt Security
The Builder sanitizes all variables injected from User Input. It surrounds User Task Instructions with specific delimiter tokens (e.g., `---USER_INPUT_START---`) to train the LLM to separate core instructions from potentially malicious user text.

## 16. Prompt Audit
The exact compiled string produced by the Prompt Builder is stored in the `TaskExecution` database record. When an incident occurs, an engineer can read the exact words the LLM was given.

## 17. Future Expansion
The architecture supports the integration of "Prompt Compilers," an AI-driven optimization step where a master LLM rewrites the human-authored templates to be more mathematically aligned with the target model's latent space before execution.

## 18. Permanent Constraints
* The Prompt Builder must enforce the Instruction Hierarchy; Task instructions can never override System instructions.
* Dynamic variable resolution must be strictly sanitized.
* Prompt templates must be versioned.
* The finalized prompt string must be permanently auditable.

---

## Never Do

* **Never** allow a User to directly modify the System, Organization, or Department prompt templates unless they have explicit `GlobalAdmin` or `OrgAdmin` RBAC roles.
* **Never** blindly concatenate User Input directly into the instruction payload without surrounding it with strong delimiter tokens.
* **Never** overwrite a prompt template in the database; always create a new version record.
* **Never** allow the Prompt Builder to bypass the Guardian validation check.

---

## Prompt Builder Constitution
The permanent Prompt Builder principles of AegisAI:
1. **The Principle of Layered Authority**: The AI must know exactly who is giving the order. System overrides Organization; Organization overrides Agent; Agent overrides User.
2. **The Principle of Immutable Words**: When an AI makes a mistake, the first question is "What exactly were you told?" The system must be able to answer that question with absolute, historical certainty.
3. **The Principle of Quarantine**: User input is treated as untrusted, hostile data. It is never allowed to mix freely with the core behavioral instructions of the system.
