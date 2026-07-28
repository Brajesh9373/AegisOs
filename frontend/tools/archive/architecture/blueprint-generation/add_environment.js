const fs = require('fs');
const oldFile = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.3.md';
let txt = fs.readFileSync(oldFile, 'utf8');

// 1. Version Bump to v2.4
txt = txt.replace(/Version: 2\.3\.0/g, 'Version: 2.4.0');
txt = txt.replace(/#  aegisOS Platform Blueprint v2\.3/g, '#  aegisOS Platform Blueprint v2.4');

// 2. Add Environment to Hierarchy lists
const oldHier1 = `The complete structural execution hierarchy operates as follows:\r\n1. Customer\r\n2. Business Outcome\r\n3. Business Goal\r\n4. Implementation Program\r\n5. Implementation Project\r\n6. Digital Team\r\n7. Workflow\r\n8. Agent\r\n9. Skill\r\n10. Task\r\n11. Action`;
const newHier1 = `The complete structural execution hierarchy operates as follows:\r\n1. Customer\r\n2. Business Outcome\r\n3. Business Goal\r\n4. Implementation Program\r\n5. Implementation Project\r\n6. Environment\r\n7. Digital Team\r\n8. Workflow\r\n9. Agent\r\n10. Skill\r\n11. Task\r\n12. Action`;
txt = txt.replace(oldHier1, newHier1);

const oldDeptHier = `The complete topological hierarchy is now explicitly defined as:\r\n1. Organization\r\n2. Department\r\n3. Workspace\r\n4. Customer\r\n5. Business Outcome\r\n6. Business Goal\r\n7. Implementation Program\r\n8. Implementation Project\r\n9. Digital Team\r\n10. Workflow\r\n11. Agent\r\n12. Skill\r\n13. Task\r\n14. Action`;
const newDeptHier = `The complete topological hierarchy is now explicitly defined as:\r\n1. Organization\r\n2. Department\r\n3. Workspace\r\n4. Customer\r\n5. Business Outcome\r\n6. Business Goal\r\n7. Implementation Program\r\n8. Implementation Project\r\n9. Environment\r\n10. Digital Team\r\n11. Workflow\r\n12. Agent\r\n13. Skill\r\n14. Task\r\n15. Action`;
txt = txt.replace(oldDeptHier, newDeptHier);

const oldProjHier = `###  Implementation Project Hierarchy\r\nThe platform operates on the following conceptual execution hierarchy:\r\n1. Customer\r\n2. Business Outcome\r\n3. Business Goal\r\n4. Implementation Program\r\n5. Implementation Project\r\n6. Digital Team\r\n7. Workflow\r\n8. Agent\r\n9. Skill\r\n10. Task\r\n11. Action`;
const newProjHier = `###  Implementation Project Hierarchy\r\nThe platform operates on the following conceptual execution hierarchy:\r\n1. Customer\r\n2. Business Outcome\r\n3. Business Goal\r\n4. Implementation Program\r\n5. Implementation Project\r\n6. Environment\r\n7. Digital Team\r\n8. Workflow\r\n9. Agent\r\n10. Skill\r\n11. Task\r\n12. Action`;
txt = txt.replace(oldProjHier, newProjHier);

// 3. Add Environment definition in Business Goal Model
const oldProjectDef = `###  Implementation Project\r\n- **Responsibility**: Translates the Program into a structured timeline of deliverables, managing global project constraints, budgets, and the allocation of Digital Teams.\r\n\r\n###  Digital Team`;
const newProjectDef = `###  Implementation Project\r\n- **Responsibility**: Translates the Program into a structured timeline of deliverables, managing global project constraints, budgets, and the allocation of Digital Teams.\r\n\r\n###  Environment\r\n- **Responsibility**: The designated execution target for the Implementation Project. It structurally stores discovered infrastructure, connection information, deployment targets, execution boundaries, environment variables, credentials references (never raw secrets), and network topology.\r\n\r\n###  Digital Team`;
txt = txt.replace(oldProjectDef, newProjectDef);

// 4. Update existing Environment definition in Canonical Platform Objects
const oldEnvObj = /###\s+Environment\r?\nFirst-class platform concept\. Represents Source Environment and Target Environment\.\r?\n-\s\*\*Supported\*\*: Development, Testing, Sandbox, Staging, Production, Cloud, On-Premise, Hybrid, Virtual Machine, Container, Kubernetes, Serverless\./;

const newEnvObj = `###  Environment\r\nFirst-class platform entity acting as the execution target for Implementation Projects. Represents Source Environments (where data is pulled from) and Target Environments (where changes are applied).\r\n- **Examples**: SAP Production, SAP QA, Salesforce Sandbox, Shopify Store, AWS Account, Azure Subscription, Kubernetes Cluster, Local Network.\r\n- **Responsibilities**: Store discovered infrastructure, store connection information, store deployment targets, store execution boundaries, store environment variables, store credentials references (never raw secrets), and store topology.`;

txt = txt.replace(oldEnvObj, newEnvObj);

fs.writeFileSync('d:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.4.md', txt);
fs.unlinkSync(oldFile);
console.log('Update complete.');
