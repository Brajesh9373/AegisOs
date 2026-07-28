# AegisAI Knowledge Architecture Specification

This document defines the definitive, permanent Knowledge Architecture for AegisAI. It establishes the rules, hierarchy, and governance of how organizational assets, documents, and standard operating procedures (SOPs) are stored, accessed, and utilized across the platform.

## 1. Knowledge Philosophy
Knowledge is the static, enduring intellectual property of an organization. Unlike transient memory, knowledge is universally reusable, strictly governed, and serves as the absolute ground truth for AI execution. Knowledge belongs exclusively to the organization; AI serves only as an authorized consumer of that knowledge.

## 2. Objectives
The Knowledge Architecture must:
* Provide a single, authoritative source of truth for organizational processes.
* Guarantee strict isolation between organizational tenants.
* Enforce RBAC and Guardian policies during knowledge retrieval.
* Ensure knowledge is fully versioned, auditable, and certified.
* Enable high-performance, contextually relevant search and retrieval.

## 3. Knowledge Architecture
The Knowledge System is a distributed, multi-tiered document and vector storage architecture. It decouples the storage of raw documents from the semantic retrieval engine. Knowledge retrieval occurs explicitly before execution, mediated entirely by Guardian, and injected as context into the Runtime.

## 4. Knowledge Ownership
* **Organizations own all knowledge**. 
* **Humans curate knowledge**; human experts author, approve, and certify knowledge assets.
* **AI never owns knowledge**; it merely queries and consumes authorized fragments.

## 5. Knowledge Hierarchy
Knowledge is organized in a strict logical hierarchy to enforce visibility and relevance:
1. Platform Knowledge
2. Organization Knowledge
3. Department Knowledge
4. Team Knowledge
5. Agent Knowledge
6. Private Knowledge

## 6. Platform Knowledge
* **Scope**: Global across the AegisAI instance.
* **Usage**: Core system capabilities, universal constraints, standard platform tutorials.
* **Example**: "How to format an AegisAI markdown response."

## 7. Organization Knowledge
* **Scope**: Bound to a specific tenant organization.
* **Usage**: Company-wide policies, brand guidelines, employee handbooks.
* **Example**: "ACME Corp's global data privacy policy."

## 8. Department Knowledge
* **Scope**: Bound to a functional department (e.g., Finance, Engineering).
* **Usage**: Departmental standards, domain-specific glossaries.
* **Example**: "Finance department expense reporting SOP."

## 9. Team Knowledge
* **Scope**: Bound to a specific sub-group or project team.
* **Usage**: Project architectures, sprint runbooks.
* **Example**: "Project Alpha deployment pipeline configuration."

## 10. Agent Knowledge
* **Scope**: Bound explicitly to a single AI assistant persona.
* **Usage**: Persona-specific instructions, customized formatting templates.
* **Example**: "The customer support bot's specific troubleshooting tree for Product X."

## 11. Private Knowledge
* **Scope**: Bound to an individual human user.
* **Usage**: Personal drafts, individualized notes, user-specific procedures.
* **Example**: "My personal checklist for reviewing quarterly reports."

## 12. Shared Knowledge
Knowledge explicitly granted cross-boundary access (e.g., Department A sharing a document with Department B). All sharing requires explicit human authorization and creates an audit trail.

## 13. Knowledge Sources
Knowledge enters the system through explicit human upload, API integration (e.g., Confluence, SharePoint), or certified AI generation (following a human review).

## 14. Internal Documents
Documents authored directly within AegisAI. These are structurally governed and natively versioned.

## 15. External Documents
Documents indexed from external sources. These are treated as read-only replicas; the source of truth remains the external system, while AegisAI holds the semantic index.

## 16. SOP Management
Standard Operating Procedures (SOPs) are a specialized class of highly structured Knowledge. They dictate exact, step-by-step execution rules that agents must follow precisely.

## 17. Runbooks
Actionable knowledge assets linking specific procedures to available Skills, effectively scripting AI workflows.

## 18. Policies
Formal governance rules (e.g., "Never disclose PII"). Policies are Knowledge assets that the Guardian engine explicitly evaluates during execution.

## 19. Standards
Organizational benchmarks (e.g., "Code formatting standards", "Brand voice guidelines") used by agents to validate generated outputs.

## 20. Procedures
Step-by-step guides for resolving specific scenarios, generally less rigid than SOPs but providing necessary contextual guidance.

## 21. Knowledge Categories
* **Declarative**: Facts and structural data.
* **Procedural**: "How-to" guides and workflows.
* **Regulatory**: Compliance and legal boundaries.
* **Reference**: Glossaries, dictionaries, API schemas.

## 22. Knowledge Classification
Every knowledge asset must be tagged with a security classification (e.g., Public, Internal, Confidential, Restricted). This acts as a secondary verification layer above RBAC.

## 23. Knowledge Visibility
Visibility is determined by the intersection of the Knowledge Hierarchy, the requester's RBAC role, and the asset's Classification.

## 24. Knowledge Permissions
Explicit permissions (Read, Write, Manage, Certify) govern who can alter or view knowledge. AI agents possess only implicit Read access dictated by their human commander's scope.

## 25. Knowledge Versioning
Every modification spawns a new, immutable version. Historical executions can be audited against the exact version of knowledge that was active at the time.

## 26. Knowledge Lifecycle
Draft → Review → Certified (Active) → Deprecated → Archived.

## 27. Knowledge Approval Workflow
Adding, modifying, or certifying High-Risk Knowledge (e.g., Legal Policies) requires a multi-step human-in-the-loop approval process.

## 28. Knowledge Publishing
The act of moving knowledge from Draft to Active. Publishing triggers re-indexing in the semantic search engine.

## 29. Knowledge Deprecation
Flagging knowledge as outdated. Deprecated knowledge is deprioritized in search results but remains accessible with a warning flag.

## 30. Knowledge Archiving
Removing knowledge from active semantic search indices. Archived knowledge is only accessible via explicit ID lookups for audit purposes.

## 31. Knowledge Search
The platform utilizes semantic vector search combined with rigid metadata pre-filtering (RBAC, Tenant ID) to retrieve relevant documents.

## 32. Knowledge Retrieval
Retrieval must always be deterministic in its access control. If the requester lacks permission, the asset is silently excluded from the retrieval set.

## 33. Knowledge Context Building
Retrieved knowledge is synthesized and injected into the Runtime execution context. It must be clearly demarcated to prevent prompt injection attacks from external documents.

## 34. Knowledge Quality
Knowledge is ranked by certification status, freshness, and human upvotes. High-quality knowledge is prioritized during retrieval.

## 35. Knowledge Certification
A formal badge applied by a Department Manager or Admin indicating the asset is the absolute, verified truth. Certified knowledge takes precedence over all other retrieved data.

## 36. Knowledge Validation
Automated jobs periodically scan knowledge for broken links, contradictory policies, and stale content, alerting owners for review.

## 37. Knowledge Monitoring
The system tracks search queries, retrieval frequency, and "knowledge gaps" (frequent queries yielding no results) to guide human authors.

## 38. Knowledge Auditing
Every read, write, certification, and sharing event is permanently logged to the Audit ledger.

## 39. Knowledge Security
Knowledge assets are encrypted at rest. Vector embeddings are isolated per tenant to prevent cross-tenant inference attacks.

## 40. Knowledge Integrity
Cryptographic hashing ensures that retrieved knowledge has not been tampered with outside of the governed publication pipeline.

## 41. Knowledge Scalability
The architecture separates metadata (RDBMS), raw text (Object Storage), and semantic embeddings (Vector DB) to scale horizontally.

## 42. Future Expansion
The architecture supports the future addition of Knowledge Graphs and autonomous knowledge gap analysis, strictly behind the Guardian perimeter.

## 43. Permanent Constraints
* Knowledge belongs to the organization.
* AI never owns Knowledge.
* Knowledge access must always be validated by Guardian.
* Knowledge must never leak across organizations.
* Knowledge must be explicitly versioned and auditable.

---

## Conceptual Definitions

* **Knowledge**: Static, declarative, enduring organizational truth (e.g., Employee Handbook).
* **Memory**: Dynamic, experiential, stateful history (e.g., "User told me to format the output as JSON yesterday").
* **Skills**: Executable capabilities and integrations (e.g., `send_email`, `query_database`).
* **Prompt**: The immediate, transient instruction provided by the user (e.g., "Draft an email to Bob").
* **Context**: The synthesized payload assembled at runtime, containing the Prompt, relevant Knowledge, recent Memory, and allowed Skills.
* **Rules**: Hardcoded application-level constraints (e.g., "File uploads max 10MB").
* **Policies**: Human-readable organizational mandates that Guardian evaluates (e.g., "Do not email external domains").

---

## Never Do

* **Never** store transient conversation history (Memory) in the Knowledge base.
* **Never** allow AI to autonomously publish or certify Knowledge without human approval.
* **Never** mix Knowledge indices across organizations.
* **Never** permit Knowledge retrieval to bypass Guardian RBAC checks.
* **Never** hard-delete Knowledge that has been utilized in a past execution; it must be archived to preserve the audit trail.
* **Never** inject raw Knowledge into the Runtime without sanitization boundaries.

---

## Knowledge Constitution
The permanent Knowledge principles of AegisAI:
1. **Absolute Truth**: Certified organizational Knowledge supersedes AI generalization, internet knowledge, and transient memory.
2. **Absolute Governance**: Every byte of knowledge accessed is verified by Guardian against the user's explicit permissions.
3. **Absolute Accountability**: The lifecycle of knowledge—creation, certification, and retrieval—is permanently traceable to human owners.
