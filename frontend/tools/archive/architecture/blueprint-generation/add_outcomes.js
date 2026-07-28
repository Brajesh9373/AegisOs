const fs = require('fs');
const oldFile = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.2.md';
let txt = fs.readFileSync(oldFile, 'utf8');

// 1. Version Bump to v2.3
txt = txt.replace(/Version: 2\.2\.0/g, 'Version: 2.3.0');
txt = txt.replace(/#  aegisOS Platform Blueprint v2\.2/g, '#  aegisOS Platform Blueprint v2.3');

// 2. Insert "Business Outcomes" section at the top of the Business Goal Model
const oldGoalModel = `##  Business Goal Model\r\n\r\nThe platform abstracts the complexity of workflow orchestration away from the customer. Customers never create workflows directly; instead, they define high-level objectives that the platform autonomously decomposes into execution graphs.`;

const newGoalModel = `##  Business Outcomes\r\n\r\naegisOS clarifies that customers never purchase agents, workflows, or implementation projects. Customers purchase **Business Outcomes**. Business Outcomes become the measurable completion units delivered by the platform.\r\n\r\nExamples of Business Outcomes include:\r\n- Successfully migrate ERP\r\n- Deploy Kubernetes\r\n- Configure Microsoft 365\r\n- Launch Shopify Store\r\n- Migrate CRM\r\n- Setup AWS Landing Zone\r\n\r\n##  Business Goal Model\r\n\r\nThe platform abstracts the complexity of workflow orchestration away from the customer. Customers never create workflows directly; instead, they define high-level objectives that the platform autonomously decomposes into execution graphs.`;

txt = txt.replace(oldGoalModel, newGoalModel);

// 3. Add Business Outcome to the hierarchy definition list in Business Goal Model
const oldCustomer = `###  Customer\r\n- **Responsibility**: The external entity defining requirements and constraints.`;
const newCustomer = `###  Customer\r\n- **Responsibility**: The external entity defining requirements and constraints.\r\n\r\n###  Business Outcome\r\n- **Responsibility**: The overarching, measurable completion unit purchased by the customer (e.g., "Successfully migrate ERP"). It serves as the ultimate benchmark for commercial and operational success.`;
txt = txt.replace(oldCustomer, newCustomer);

// 4. Update all 3 instances of the Hierarchy lists
// Instance A: Business Goal Model
const oldHier1 = `The complete structural execution hierarchy operates as follows:\r\n1. Customer\r\n2. Business Goal\r\n3. Implementation Program\r\n4. Implementation Project\r\n5. Digital Team\r\n6. Workflow\r\n7. Agent\r\n8. Skill\r\n9. Task\r\n10. Action`;
const newHier1 = `The complete structural execution hierarchy operates as follows:\r\n1. Customer\r\n2. Business Outcome\r\n3. Business Goal\r\n4. Implementation Program\r\n5. Implementation Project\r\n6. Digital Team\r\n7. Workflow\r\n8. Agent\r\n9. Skill\r\n10. Task\r\n11. Action`;
txt = txt.replace(oldHier1, newHier1);

// Instance B: Department Section
const oldDeptHier = `The complete topological hierarchy is now explicitly defined as:\r\n1. Organization\r\n2. Department\r\n3. Workspace\r\n4. Customer\r\n5. Business Goal\r\n6. Implementation Program\r\n7. Implementation Project\r\n8. Digital Team\r\n9. Workflow\r\n10. Agent\r\n11. Skill\r\n12. Task\r\n13. Action`;
const newDeptHier = `The complete topological hierarchy is now explicitly defined as:\r\n1. Organization\r\n2. Department\r\n3. Workspace\r\n4. Customer\r\n5. Business Outcome\r\n6. Business Goal\r\n7. Implementation Program\r\n8. Implementation Project\r\n9. Digital Team\r\n10. Workflow\r\n11. Agent\r\n12. Skill\r\n13. Task\r\n14. Action`;
txt = txt.replace(oldDeptHier, newDeptHier);

// Instance C: Implementation Project Hierarchy (under Digital Workforce)
const oldProjHier = `###  Implementation Project Hierarchy\r\nThe platform operates on the following conceptual execution hierarchy:\r\n1. Customer\r\n2. Business Goal\r\n3. Implementation Program\r\n4. Implementation Project\r\n5. Digital Team\r\n6. Workflow\r\n7. Agent\r\n8. Skill\r\n9. Task\r\n10. Action`;
const newProjHier = `###  Implementation Project Hierarchy\r\nThe platform operates on the following conceptual execution hierarchy:\r\n1. Customer\r\n2. Business Outcome\r\n3. Business Goal\r\n4. Implementation Program\r\n5. Implementation Project\r\n6. Digital Team\r\n7. Workflow\r\n8. Agent\r\n9. Skill\r\n10. Task\r\n11. Action`;
txt = txt.replace(oldProjHier, newProjHier);

fs.writeFileSync('d:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.3.md', txt);
fs.unlinkSync(oldFile);
console.log('Update complete.');
