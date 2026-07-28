const fs = require('fs');
const oldFile = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.7.md';
let txt = fs.readFileSync(oldFile, 'utf8');

// 1. Version Bump
txt = txt.replace(/Version: 2\.7\.0/g, 'Version: 2.8.0');
txt = txt.replace(/#  aegisOS Platform Blueprint v2\.7/g, '#  aegisOS Platform Blueprint v2.8');

// 2. Extend Business Outcome & Success Criteria
const oldSuccessCriteria = /##  Success Criteria[\s\S]*?(?=##  Business Goal Model)/;
const newSuccessCriteria = `##  Success Criteria\r\n\r\nEvery Business Outcome fundamentally mandates the definition of explicitly measurable Success Criteria. The platform fundamentally distances itself from measuring completion purely by task volume or agent execution cycles; instead, an Implementation is strictly deemed complete only when its defined Success Criteria are structurally satisfied.\r\n\r\nEvery Business Outcome must explicitly define:\r\n- **Completion Rules**: Deterministic thresholds denoting task finality.\r\n- **Validation Rules**: Scripts and tests proving environmental integrity.\r\n- **Acceptance Rules**: Conditions under which a human operator accepts the deliverable.\r\n- **Evidence Requirements**: The exact artifact types (screenshots, logs) required to prove completion.\r\n- **Approval Requirements**: The strict cryptographic sign-off chain mandated for execution.\r\n- **Rollback Requirements**: The fail-safe state restoration protocols if criteria are not met.\r\n- **Business Metrics**: The commercial or operational KPIs validating the ultimate objective.\r\n\r\nWhen these structural thresholds are met, the Success Criteria become the official, cryptographic completion signal for the project, triggering final validation and deployment phases.\r\n\r\n`;
txt = txt.replace(oldSuccessCriteria, newSuccessCriteria);

// 3. Integrate into Implementation Project
const oldImplProject = /###  Implementation Project\r?\n- \*\*Responsibility\*\*: Translates the Program into a structured timeline of deliverables, managing global project constraints, budgets, and the allocation of Digital Teams\./g;
const newImplProject = `###  Implementation Project\r\n- **Responsibility**: Translates the Program into a structured timeline of deliverables, managing global project constraints, budgets, and the allocation of Digital Teams. Execution halts iteratively until the explicit Success Criteria defined by the Business Outcome are achieved.`;
txt = txt.replace(oldImplProject, newImplProject);

// 4. Integrate into Validation
const oldValidation = /###  11\. Validation\r?\n- \*\*Responsibility\*\*: Evidentiary verification that the mutated live environment strictly satisfies the structural contracts and the declarative Business Outcome\./g;
const newValidation = `###  11. Validation\r\n- **Responsibility**: Evidentiary verification that the mutated live environment strictly satisfies the structural contracts and the predefined Validation Rules of the Business Outcome's Success Criteria.`;
txt = txt.replace(oldValidation, newValidation);

// 5. Integrate into Evidence
const oldEvidenceCap = /###  Evidence\r?\n- \*\*Purpose\*\*: Ensure every implementation step produces verifiable proof of work\./g;
const newEvidenceCap = `###  Evidence\r\n- **Purpose**: Ensure every implementation step produces verifiable proof of work strictly aligned with the Evidence Requirements dictated by the Business Outcome's Success Criteria.`;
txt = txt.replace(oldEvidenceCap, newEvidenceCap);

// 6. Integrate into Approval Gates
const oldApprovalGates = /- \*\*Approval Gates\*\*: Digital Employees pause autonomous execution when encountering high-risk state changes, forwarding cryptographic payloads to Human Employees or Partners for explicit sign-off\./g;
const newApprovalGates = `- **Approval Gates**: Digital Employees pause autonomous execution when encountering high-risk state changes, forwarding cryptographic payloads to Human Employees or Partners for explicit sign-off in strict accordance with the Approval Requirements defined by the Business Outcome.`;
txt = txt.replace(oldApprovalGates, newApprovalGates);

// 7. Integrate into Workflow
const oldWorkflowCap = /###  Workflow\r?\n- \*\*Purpose\*\*: Stateful DAG orchestration\./g;
const newWorkflowCap = `###  Workflow\r\n- **Purpose**: Stateful DAG orchestration parameterized by the precise Completion Rules and Rollback Requirements defined in the Business Outcome's Success Criteria.`;
txt = txt.replace(oldWorkflowCap, newWorkflowCap);

fs.writeFileSync('d:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.8.md', txt);
fs.unlinkSync(oldFile);
console.log('Update complete.');
