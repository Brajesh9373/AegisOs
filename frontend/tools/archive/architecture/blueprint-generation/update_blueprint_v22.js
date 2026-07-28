const fs = require('fs');
const oldFile = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.1.md';
let txt = fs.readFileSync(oldFile, 'utf8');

// 1. Version Bump
txt = txt.replace(/Version: 2\.1\.0/g, 'Version: 2.2.0');
txt = txt.replace(/#  aegisOS Platform Blueprint v2\.1/g, '#  aegisOS Platform Blueprint v2.2');

// 2. Business Goal Model
const oldBusinessGoal = /###\s+Business Goal\r?\n- \*\*Responsibility\*\*: Represents the ultimate customer-defined outcome and absolute success criteria\. This is the highest-level declarative directive \(e\.g\., "Migrate CRM to HubSpot"\)\./;
const newBusinessGoal = `###  Customer\r\n- **Responsibility**: The external entity defining requirements and constraints.\r\n\r\n###  Business Goal\r\n- **Responsibility**: Represents the ultimate customer-defined outcome and absolute success criteria. This is the highest-level declarative directive (e.g., "Migrate CRM to HubSpot").\r\n\r\n###  Implementation Program\r\n- **Responsibility**: The macro-level orchestration container managing multiple inter-dependent Implementation Projects.`;
txt = txt.replace(oldBusinessGoal, newBusinessGoal);

// Update Hierarchy list in Business Goal section
const oldHier1 = `The complete structural execution hierarchy operates as follows:`;
const newHier1 = `The complete structural execution hierarchy operates as follows:\r\n1. Customer\r\n2. Business Goal\r\n3. Implementation Program\r\n4. Implementation Project\r\n5. Digital Team\r\n6. Workflow\r\n7. Agent\r\n8. Skill\r\n9. Task\r\n10. Action`;
txt = txt.replace(oldHier1, newHier1);

// Update Department Hierarchy list
const oldDeptHier = /The complete topological hierarchy is now explicitly defined as:[\s\S]*?(?=###\s+Responsibilities)/;
const newDeptHier = `The complete topological hierarchy is now explicitly defined as:\r\n1. Organization\r\n2. Department\r\n3. Workspace\r\n4. Customer\r\n5. Business Goal\r\n6. Implementation Program\r\n7. Implementation Project\r\n8. Digital Team\r\n9. Workflow\r\n10. Agent\r\n11. Skill\r\n12. Task\r\n13. Action\r\n\r\n`;
txt = txt.replace(oldDeptHier, newDeptHier);

// Update Implementation Project Hierarchy list
const oldProjHier = /###\s+Implementation Project Hierarchy[\s\S]*?(?=###\s+Implementation Templates)/;
const newProjHier = `###  Implementation Project Hierarchy\r\nThe platform operates on the following conceptual execution hierarchy:\r\n1. Customer\r\n2. Business Goal\r\n3. Implementation Program\r\n4. Implementation Project\r\n5. Digital Team\r\n6. Workflow\r\n7. Agent\r\n8. Skill\r\n9. Task\r\n10. Action\r\n\r\n`;
txt = txt.replace(oldProjHier, newProjHier);

// 3. New Canonical Definitions (Discovery Engine, Assessment Engine, Planning Engine)
// We replace the old Planner with Planning Engine and add the other two
const engines = `###  Discovery Engine\r\n**Purpose**: Automatically discover customer environments.\r\n- **Responsibilities**: System Discovery, Infrastructure Discovery, Application Discovery, API Discovery, Database Discovery, Identity Discovery, Network Discovery, Configuration Discovery, Dependency Discovery, Connector Discovery, Version Discovery, Risk Discovery.\r\n- **Outputs**: Discovery Report, Asset Inventory, Dependency Map, Environment Profile.\r\n\r\n###  Assessment Engine\r\n**Purpose**: Analyze discovered environments.\r\n- **Responsibilities**: Complexity Analysis, Compatibility Analysis, Risk Analysis, Migration Readiness, Compliance Analysis, Best Practice Analysis, Gap Analysis.\r\n- **Outputs**: Assessment Report, Risk Report, Migration Score, Complexity Score, Estimated Effort.\r\n\r\n###  Planning Engine\r\n**Purpose**: Convert Business Goals into executable implementation plans.\r\n- **Responsibilities**: Execution Planning, Timeline Planning, Dependency Planning, Rollback Planning, Approval Planning, Resource Planning, Digital Team Assignment.\r\n- **Output**: Implementation Plan.\r\n\r\n`;
txt = txt.replace(/###\s+Planner[\s\S]*?(?=###\s+Workflow\r?\nThe stateful DAG)/, engines);

// Remove the old Planner from Capability Map and insert new engines
const mapEngines = `###  Discovery Engine\r\n- **Purpose**: Automatically discover customer environments.\r\n- **Outputs**: Discovery Report, Asset Inventory, Dependency Map, Environment Profile.\r\n\r\n###  Assessment Engine\r\n- **Purpose**: Analyze discovered environments.\r\n- **Outputs**: Assessment Report, Risk Report, Migration Score, Complexity Score, Estimated Effort.\r\n\r\n###  Planning Engine\r\n- **Purpose**: Convert Business Goals into executable implementation plans.\r\n- **Responsibilities**: Execution, Timeline, Dependency, Rollback, Approval, Resource Planning, Digital Team Assignment.\r\n- **Outputs**: Implementation Plan.\r\n\r\n`;
txt = txt.replace(/###\s+Planner[\s\S]*?(?=###\s+Workflow[\r\n]+-\s\*\*Purpose\*\*: Stateful DAG)/, mapEngines);

// 4. Canonical Platform Objects
const platformObjects = `##  Canonical Platform Objects\r\n\r\n###  Business Goal\r\nCustomer-defined target outcome.\r\n\r\n###  Implementation Program\r\nMacro-orchestration container across projects.\r\n\r\n###  Implementation Project\r\nStructured timeline of deliverables.\r\n\r\n###  Discovery Report\r\nAggregated output of environment discovery.\r\n\r\n###  Assessment Report\r\nAnalysis of complexity, gaps, and readiness.\r\n\r\n###  Implementation Plan\r\nDeterministic roadmap generated by the Planning Engine.\r\n\r\n###  Implementation Graph\r\nAn implementation project consists of multiple workflows.\r\n- **Hierarchy**: Implementation Graph -> Workflow -> Task Graph -> Execution Graph\r\n- **Purpose**: Managing macro-orchestration responsibilities across the execution stack.\r\n\r\n###  Environment\r\nFirst-class platform concept. Represents Source Environment and Target Environment.\r\n- **Supported**: Development, Testing, Sandbox, Staging, Production, Cloud, On-Premise, Hybrid, Virtual Machine, Container, Kubernetes, Serverless.\r\n\r\n###  Asset Inventory\r\nInput to Assessment and Planning. Tracks Applications, Servers, Users, Roles, Databases, Products, Orders, Files, Certificates, Secrets, Configurations, Policies, Workflows, Infrastructure.\r\n\r\n###  Risk Report\r\nEvaluation of structural threats.\r\n\r\n###  Execution Evidence\r\nEnterprise-grade proof of work, collected automatically throughout execution. Includes Screenshots, API Responses, Logs, Configuration Diffs, Database Changes, Deployment Logs, Terminal Output, Reports, Validation Results, Audit Evidence.\r\n\r\n###  Deployment Artifact\r\nImmutable packaged bundle ready for production.\r\n\r\n###  Experience Library\r\nCaptures organizational implementation experience for continuous improvement. Includes Lessons Learned, Successful Patterns, Failure Patterns, Optimizations, Recommendations, Playbooks, Reusable Strategies.\r\n\r\n`;
txt = txt.replace(/(##\s+Marketplace)/, platformObjects + '$1');

// 5. Expand Implementation Templates
const oldTemplates = /Implementation Templates are prebuilt combinations of Agents, Skills, Workflows, Knowledge, and Memory designed for specific domains\./;
const newTemplates = `Implementation Templates are reusable platform assets designed for specific domains. Each template may include:\r\n- Discovery Rules\r\n- Assessment Rules\r\n- Planning Rules\r\n- Implementation Graph\r\n- Digital Teams\r\n- Knowledge\r\n- Memory\r\n- Policies\r\n- Approval Gates\r\n- Evidence Rules\r\n- Validation Rules\r\n- Deployment Rules`;
txt = txt.replace(oldTemplates, newTemplates);

// 6. Universal Implementation Lifecycle
const newLifecycle = `##  Universal Implementation Lifecycle\r\n\r\nThis is the canonical implementation lifecycle:\r\n1. **Customer Request**\r\n2. **Business Goal**\r\n3. **Discovery**\r\n4. **Assessment**\r\n5. **Planning**\r\n6. **Architecture Validation**\r\n7. **Implementation Graph**\r\n8. **Environment Preparation**\r\n9. **Digital Team Provisioning**\r\n10. **Knowledge Loading**\r\n11. **Execution**\r\n12. **Validation**\r\n13. **Evidence Collection**\r\n14. **Deployment**\r\n15. **Verification**\r\n16. **Optimization**\r\n17. **Knowledge Capture**\r\n18. **Experience Library**\r\n19. **Completed**\r\n\r\n`;
txt = txt.replace(/##\s+Implementation Lifecycle[\s\S]*?(?=##\s+Human Collaboration)/, newLifecycle);

// 7. Future Platform Modules
const futureModules = `##  Future Platform Modules\r\n\r\nFuture conceptual modules in the platform roadmap include:\r\n- Discovery\r\n- Assessment\r\n- Planning\r\n- Environment\r\n- Assets\r\n- Evidence\r\n- Experience\r\n- Guardian\r\n- Deployment\r\n- Validation\r\n\r\nThese are conceptual only and strictly preserve current package architecture.\r\n\r\n`;
txt = txt.replace(/(##\s+Platform Layers)/, futureModules + '$1');

fs.writeFileSync('d:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.2.md', txt);
fs.unlinkSync(oldFile);
console.log('Update complete.');
