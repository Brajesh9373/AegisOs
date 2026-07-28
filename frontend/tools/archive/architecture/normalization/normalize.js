const fs = require('fs');
const oldFile = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v3.0.md';
let txt = fs.readFileSync(oldFile, 'utf8');

// 1. Version Bump
txt = txt.replace(/Version: 3\.0\.0/g, 'Version: 3.1.0');
txt = txt.replace(/#  aegisOS Platform Blueprint v3\.0/g, '#  aegisOS Platform Blueprint v3.1');

// 2. Canonical Hierarchy Normalization
const oldHier1 = /###  Implementation Project Hierarchy\r?\nThe platform operates on the following conceptual execution hierarchy:[\s\S]*?(?=##\s+Hybrid Workforce)/;
const newHier1 = `###  Topological Hierarchy Cross-Reference\r\nFor the structural execution hierarchy, see **Canonical Topological Hierarchy**.\r\n\r\n`;
txt = txt.replace(oldHier1, newHier1);

const oldHier2 = /The complete structural execution hierarchy operates as follows:[\s\S]*?(?=###  Customer)/;
const newHier2 = `For the comprehensive execution topology, see **Canonical Topological Hierarchy**. Note that the hierarchy represents business and architectural ownership. It is NOT a strict runtime execution tree. An Implementation Project may reference multiple Environments, and Digital Teams may operate across multiple Environments within the same project. The Environment represents an execution boundary, not a physical restriction on Agent routing.\r\n\r\n`;
txt = txt.replace(oldHier2, newHier2);

const canonicalHierarchy = `##  Canonical Topological Hierarchy\r\n\r\nThe complete topological hierarchy is now explicitly defined as a unified model representing business and architectural ownership:\r\n1. Organization\r\n2. Department\r\n3. Workspace\r\n4. Customer\r\n5. Business Outcome\r\n6. Business Goal\r\n7. Implementation Program\r\n8. Implementation Project\r\n9. Environment\r\n10. Digital Team\r\n11. Workflow\r\n12. Agent\r\n13. Skill\r\n14. Task\r\n15. Action\r\n\r\n*Note: This is NOT a runtime execution tree. An Implementation Project may reference multiple Environments. Digital Teams may operate across multiple Environments within the same project. Environment is an execution boundary, not a restriction on Agent execution.*\r\n\r\n`;
txt = txt.replace(/The complete topological hierarchy is now explicitly defined as:[\s\S]*?15\. Action\r?\n/, canonicalHierarchy);

// 3. Move Implementation Templates out of Digital Workforce.
const oldTemplates = /###  Implementation Templates\r?\nImplementation Templates are reusable platform assets designed for specific domains\.[\s\S]*?(?=##\s+Hybrid Workforce)/;
txt = txt.replace(oldTemplates, "");

// 4. Ensure Marketplace references Platform Assets correctly.
const marketplaceUpdate = `###  Platform Asset Model\r\nAll reusable assets (Implementation Templates, Knowledge Packs, Compliance Packs, Industry Packs, Policies, Playbooks, Validation Packs, Connector Packs) are strictly treated as **Platform Assets** distributed through the Marketplace. They are not classified as Digital Workforce components.\r\n\r\n`;
txt = txt.replace(/(##\s+Marketplace\r?\n\r?\n)/, `$1${marketplaceUpdate}`);

// 5. Replace duplicate definitions with references.
txt = txt.replace(/###  Workflow\r?\n- \*\*Purpose\*\*: Stateful DAG orchestration parameterized[\s\S]*?(?=###\s+Agent)/, `###  Workflow\r\n*See Canonical Definition: Workflow.*\r\n\r\n`);
txt = txt.replace(/###  Environment\r?\nFirst-class platform entity acting as the execution boundary[\s\S]*?(?=###\s+Asset Inventory)/, `###  Environment\r\n*See Canonical Definition: Environment.*\r\n\r\n`);

fs.writeFileSync('d:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v3.1.md', txt);
console.log('Document Normalized.');
