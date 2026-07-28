# AegisAI Context Builder Architecture Specification

This document defines the definitive, permanent Context Builder Architecture for AegisAI. It establishes the mechanical pipeline that aggregates, filters, and formats diverse data streams into a singular, deterministic payload ready for LLM consumption.

## 1. Context Builder Philosophy
An LLM is only as intelligent as the data it is provided at the exact moment of inference. The Context Builder is a deterministic data pipeline. It must operate with mechanical precision, treating prompt assembly not as string concatenation, but as a rigid ETL (Extract, Transform, Load) process bounded by hard token limits and absolute security parameters.

## 2. Objectives
The Context Builder Architecture must:
* Assemble the LLM payload synchronously before any AI execution begins.
* Guarantee 100% RBAC compliance during data retrieval.
* Provide reproducible context states for debugging and auditing.
* Prevent context window overflow via intelligent compression and truncation.

## 3. Context Assembly
The Assembly Pipeline executes a sequence of specialized data fetchers in parallel:
1. `PromptFetcher`: Retrieves System, Organization, and Agent prompts.
2. `SkillFetcher`: Retrieves allowed Tool JSON schemas.
3. `KnowledgeFetcher`: Executes RAG queries against the Vector DB.
4. `MemoryFetcher`: Retrieves the episodic interaction history.
These raw data streams are then passed to the Resolver.

## 4. Context Resolution
The Resolver resolves dynamic variables within the fetched templates (e.g., replacing `{{current_date}}` or `{{user_name}}` with hard values). Missing required variables cause the pipeline to fail fast.

## 5. Context Ranking
Once all potential context is gathered, it is ranked by importance. System Prompts and Security Policies have infinite weight. RAG results are ranked by cosine similarity. Memory is ranked by recency and relevance to the current Task.

## 6. Context Filtering
The Filter layer drops any ranked context block that violates active Guardian constraints (e.g., scrubbing PII if the external LLM provider is not HIPAA certified).

## 7. Context Validation
The pipeline validates the final context blocks against the specific target LLM's token limits (e.g., 128k for GPT-4o). It counts tokens using a fast, local tokenizer (e.g., `tiktoken`).

## 8. Context Compression
If the total token count exceeds the limit, the Compression layer activates. It performs aggressive semantic truncation:
* Older Memory blocks are dropped.
* Low-relevance RAG chunks are dropped.
* If necessary, remaining Memory is passed through a local, small LLM to generate a dense summary.

## 9. Context Ordering
The finalized data blocks are ordered exactly as required by the LLM Provider's API schema (e.g., OpenAI's Chat Completion format). System prompts always occupy the `role: system` array, while user inputs occupy the `role: user` array.

## 10. Context Caching
To reduce latency and database load, frequently assembled blocks (like Organization System Prompts or static Tool Schemas) are cached in Redis. Dynamic data (Memory, Task Input) is never cached across executions.

## 11. Context Security
The pipeline physically cannot fetch data that the initiating User does not have RBAC access to. The `user_id` and `tenant_id` are hard-coded into the database query predicates used by the Fetchers.

## 12. Runtime Integration
The Context Builder acts as a synchronous dependency for the Task Engine. The Engine requests a payload, the Builder returns it, and the Engine forwards it to the AI Provider.

## 13. Guardian Integration
The Builder optionally calls Guardian during the Filtering stage to ensure no sensitive data is leaked into the payload before it leaves the enterprise boundary.

## 14. Future Expansion
The architecture supports the future addition of "Multi-Modal Context," allowing the pipeline to natively embed base64-encoded images, audio clips, and UI screenshots directly into the context stream alongside text.

## 15. Permanent Constraints
* Context is fully assembled *before* AI execution begins.
* Context assembly must mathematically guarantee no unauthorized data is included.
* Context assembly must be 100% reproducible for a given timestamp and database state.
* The exact assembled payload must be traceable and auditable.
* Token counting must be performed locally before network transmission.

---

## Never Do

* **Never** rely on the external LLM provider to truncate context; you lose control over what data is dropped (e.g., it might drop a critical security prompt).
* **Never** allow the Builder to fetch Knowledge or Memory using a superuser database role; it must always impersonate the invoking User's RBAC scope.
* **Never** inject unstructured user input directly into the `System` prompt context area, as this enables direct Prompt Injection.
* **Never** cache Context payloads that contain ephemeral task data or PII.

---

## Context Builder Constitution
The permanent Context Builder principles of AegisAI:
1. **The Principle of the Rigid Funnel**: Vast amounts of enterprise data enter the top; only the highly concentrated, perfectly secured, and strictly relevant data exits the bottom.
2. **The Principle of Prioritized Survival**: When token space is exhausted, the system's rules survive, the task's requirements survive, and everything else is gracefully destroyed.
3. **The Principle of Auditable Assembly**: The black box of AI begins at the provider's API. Everything leading up to that API call—every string, variable, and RAG chunk—must be perfectly documented and deterministic.
