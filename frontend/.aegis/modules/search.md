# AegisAI Search Architecture Specification

This document defines the definitive, permanent Search Architecture for AegisAI. It establishes the indexing strategies, query execution pathways, and the absolute necessity of integrating strict Role-Based Access Control (RBAC) at the deepest level of the search engine.

## 1. Search Philosophy
Search is the primary UX paradigm of an AI OS. However, search is fundamentally a data retrieval mechanism, which makes it a critical security vector. A user or Agent can only find what they are legally permitted to see. The Search Architecture prioritizes data isolation and security over sheer retrieval speed.

## 2. Search Architecture
The Search Engine operates as a federated layer. It unifies results from a Vector Database (for semantic RAG queries), a structured text search engine like Elasticsearch/OpenSearch (for Audit and metadata), and the primary relational database (for exact ID lookups). The API Gateway intercepts the query, injects the user's RBAC scope, and distributes the query to the underlying engines.

## 3. Global Search
A unified search bar in the UI. It allows an authorized user to query across Workspaces, Agents, Knowledge, and Tasks simultaneously, returning a categorized list of results.

## 4. Organization Search
Queries explicitly scoped to a single Tenant/Organization, forming the absolute boundary for any query executed by standard users or Agents.

## 5. Agent Search
Allows users to discover available AI personas by querying their capabilities, descriptions, and assigned Workspaces.

## 6. Knowledge Search
Queries directed at the document repository. Uses a hybrid approach: Keyword search for titles/metadata and Semantic search for the actual content of the documents.

## 7. Memory Search
Queries directed at an Agent's episodic history. Agents use this internally during Task execution to retrieve context from past interactions.

## 8. Skill Search
A registry lookup for available integrations and tools (e.g., searching for "SAP" to find the SAP Connector plugin).

## 9. Task Search
Queries against the Task Engine ledger. Heavily relies on structured filters (e.g., finding all `Failed` tasks assigned to `Agent X` between `Date A` and `Date B`).

## 10. Audit Search
A specialized, highly restricted search against the immutable Audit Ledger, optimized for eDiscovery, compliance reporting, and Boolean logic.

## 11. Semantic Search
Utilizes vector embeddings to find results based on meaning rather than exact word matches (e.g., searching "employee termination" returning a document titled "Offboarding Procedure").

## 12. Keyword Search
Utilizes traditional TF-IDF or BM25 algorithms for exact phrase matching, crucial for finding specific Error Codes or exact Names.

## 13. Filters
All search APIs must support complex Boolean filtering (`AND`, `OR`, `NOT`) applied as pre-filters *before* the semantic/keyword scoring to ensure accuracy and respect RBAC.

## 14. Ranking
Results are scored and ranked. The engine applies a boosting multiplier based on Recency and Context (e.g., if searching within a specific Workspace, documents from that Workspace rank higher).

## 15. Permissions
The core security constraint. Every indexed document contains an `acl` (Access Control List) or `tenant_id` field. The Search Engine physically cannot return a document if the querying user's dynamically injected RBAC token does not intersect with the document's ACL.

## 16. Context Awareness
If an Agent executes a search while actively working on "Project X", the Engine implicitly boosts results related to "Project X".

## 17. Indexing Strategy
Data is indexed asynchronously. When a document is uploaded, a background worker parses it, generates embeddings, and pushes it to the Search Engine. The primary database remains the source of truth.

## 18. Refresh Strategy
Indexes are updated in near-real-time. When a record is deleted in the primary database, a high-priority event is dispatched to immediately tombstone the record in the Search Engine.

## 19. Monitoring
The system monitors query latency, the ratio of "zero result" queries, and the health of the background indexing workers.

## 20. Audit
Every search query executed by a Human or an Agent is logged in the Audit Ledger. The log includes the raw query string and the filters applied.

## 21. Future Expansion
The architecture supports the future addition of "Generative Search," where the Search Engine does not just return documents, but synthesizes a direct answer from the top N results, complete with citations.

## 22. Permanent Constraints
* Search must strictly evaluate RBAC at the query level.
* Search must absolutely respect tenant/organization ownership boundaries.
* Search must never leak the existence of unauthorized data (e.g., returning a title but blocking the body).
* Search queries must be permanently auditable.
* The Search Engine must fail closed (return zero results) if the RBAC context is missing.

---

## Never Do

* **Never** execute a search query and then filter the results in application memory; filtering must happen at the database/index level to prevent data leaks via pagination or scoring algorithms.
* **Never** sync sensitive secrets (passwords, API keys) into the Search Engine index.
* **Never** use a single, globally shared index without strict, mandatory routing keys that guarantee tenant isolation.
* **Never** allow an Agent to dynamically construct the raw elastic/SQL query string; the Runtime must sanitize and map the Agent's intent into a safe query object.

---

## Search Constitution
The permanent Search principles of AegisAI:
1. **The Principle of Silent Denial**: If a user does not have permission to see a document, the Search Engine must act as if the document does not exist. No hints, no errors, just silence.
2. **The Principle of Pre-Filtering**: Security is a filter applied *before* the search begins, never an afterthought applied to the results.
3. **The Principle of Traced Intent**: A search query is a declaration of intent to find information. That intent must be logged, as knowing *what* a user was looking for is often as critical as knowing what they found.
