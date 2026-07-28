# Implementation Template Standard

## Purpose

The **Implementation Template Standard** establishes the universal blueprint for all repeatable automation solutions packaged and distributed via the AegisAI Marketplace. Because an Implementation Template represents a massive payload of automated intelligence, workflows, and digital labor capable of mutating enterprise systems, every template must adhere strictly to this structural specification to guarantee predictable, safe, and governable execution.

---

## 1. The Implementation Template Contract

Every Template submitted to the Marketplace must mathematically conform to the following schema:

### 1.1 Identity & Categorization

- **Identity:** A globally unique, semantic identifier (e.g., `aegis.marketplace.aws.eks_cluster_deployment`).
- **Name:** A human-readable, business-friendly title.
- **Category:** The domain classification (e.g., Cloud Infrastructure, CRM Migration, DevOps, HRMS Onboarding).
- **Versioning:** Strict semantic versioning (SemVer) mapped to the internal capabilities of the AegisAI platform.

### 1.2 Compatibility Profile

- **Supported Platforms:** The exact external systems the template manipulates (e.g., AWS, Salesforce, GitHub).
- **Supported Versions:** The explicitly supported API/SDK versions of the target platforms.
- **Supported Environments:** The execution contexts the template can run in (e.g., Development, Staging, Production).

### 1.3 Strategic Alignment

- **Business Outcome:** The macro-level business value delivered upon completion (e.g., "Establish a scalable, SOC2 compliant Kubernetes cluster").
- **Implementation Scope:** The strict boundaries of what the template _will_ and _will not_ do.
- **Prerequisites:** Environmental or licensing requirements that must be met before execution (e.g., AWS Account provisioned).
- **Dependencies:** Other Marketplace templates or internal packages this template relies upon.

### 1.4 Digital Resource Allocation

- **Digital Teams Required:** The specific compositions of Digital Teams needed (e.g., 1x Cloud Architect Team, 1x QA Team).
- **Digital Employees Required:** The exact agent personas required (e.g., "Terraform Execution Agent").
- **Skills Required:** The granular technical Skills the assigned Agents must possess to execute the Workflows.
- **Workflows:** The Directed Acyclic Graphs (DAGs) representing the execution logic.
- **Knowledge Packs:** The bundled contextual RAG artifacts, SOPs, and prompt constraints specific to this template.

### 1.5 Governance & Safety

- **Validation Rules:** The exact deterministic checks performed post-execution to prove success.
- **Evidence Requirements:** The specific cryptographic receipts and logs that must be generated for Audit.
- **Approval Points:** Explicitly defined Guardian tollgates where Human Managers must intervene and authorize progress.
- **Rollback Strategy:** The deterministic logic required to safely invert and undo the entire template's execution if validation fails.
- **Recovery Strategy:** The fallback logic executed if a non-fatal disruption occurs mid-deployment.

### 1.6 Economics & Complexity

- **Estimated Duration:** The projected Time-to-Complete (e.g., 4 Hours).
- **Estimated Cost:** The projected AI token burn and underlying infrastructure costs.
- **Complexity:** A graded score (Low/Medium/High/Extreme) denoting the architectural risk of the deployment.

### 1.7 Security & Compliance

- **Security Requirements:** Required IAM roles, credential access scopes, and vulnerability scanning mandates.
- **Compliance Requirements:** The enterprise regulatory standards the template inherently satisfies (e.g., HIPAA, GDPR, ISO 27001).

### 1.8 Delivery & Closure

- **Outputs:** The exact technical artifacts shipped (e.g., infrastructure, migrated data, deployed microservices).
- **Reports:** The human-readable summaries generated for the Executive Dashboard.
- **Success Criteria:** The absolute boolean conditions defining "Done".

---

## 2. The Template Lifecycle

To protect consuming organizations, Implementation Templates undergo a rigid, cryptographic lifecycle managed by the Marketplace Registry.

1. **Draft:** The template is under active development by Ecosystem Engineering. It cannot be instantiated.
2. **Testing:** The template is actively executing dry-runs in isolated sandbox environments, validating its Rollback and Recovery strategies.
3. **Certified:** The template has passed strict Architectural, Security, and QA reviews by the Chief Architect and Guardian engines.
4. **Published:** The template is cryptographically signed and available for download and instantiation via the Marketplace UI.
5. **Deprecated:** The template is marked for sunset. Existing instantiations may run, but new projects cannot select this template.
6. **Archived:** The template is permanently disabled and removed from the active Marketplace index, retained purely for historical audit traceability.

---

## Implementation Mapping

- **Owner Package:** [To Be Defined]
- **Owner Modules:** [To Be Defined]
- **Related Packages:** [To Be Defined]
- **Required Contracts:** [To Be Defined]
- **Required Types:** [To Be Defined]
- **Required Runtime Components:** [To Be Defined]
- **Required Builder Components:** [To Be Defined]
- **Required APIs:** [To Be Defined]
- **Required Database Models:** [To Be Defined]
- **Required Workflows:** [To Be Defined]
- **Required Skills:** [To Be Defined]
- **Required Tests:** [To Be Defined]
- **Verification Commands:** [To Be Defined]
- **Roadmap Phase:** [To Be Defined]
- **Implementation Status:** [Not Started | In Progress | Completed | Frozen]
