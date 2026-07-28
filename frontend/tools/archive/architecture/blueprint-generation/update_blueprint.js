const fs = require('fs');
const file = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v1.0.md';
let txt = fs.readFileSync(file, 'utf8');

txt = txt.replace('Version: 1.0.0', 'Version: 2.0.0');
txt = txt.replace('#  aegisOS Platform Blueprint v1.0', '#  aegisOS Platform Blueprint v2.0');

const oldMission = `###  Mission\r\nTo provide an uncompromisingly secure, resilient, and extensible architecture that bridges human intention with autonomous agent execution, ensuring absolute compliance and transparency.\r\n`;
const newMission = `###  Mission\r\n**Universal AI Implementation Operating System**\r\n\r\nWherever software implementation, onboarding, migration, configuration, deployment, or operational setup currently requires human consultants, aegisOS provides autonomous AI teams capable of completing the implementation.\r\n\r\nExamples include:\r\n- ERP\r\n- CRM\r\n- HRMS\r\n- E-commerce\r\n- Cloud Infrastructure\r\n- DevOps\r\n- Finance\r\n- Security\r\n- Internal Enterprise Software\r\n\r\n*ERP is only Phase 1.*\r\n`;

// Since line endings might vary, let's use regex for replacements to be safe.

txt = txt.replace(/###\s+Mission[\s\S]*?(?=###\s+Vision)/, newMission + '\n');

const philosophyAndModel = `###  Core Product Philosophy\r\naegisOS does NOT sell:\r\n- Chatbots\r\n- AI Assistants\r\n- Prompting\r\n\r\naegisOS sells completed implementation outcomes.\r\n\r\nCustomers define objectives.\r\n\r\nAI teams perform the work.\r\n\r\n###  Business Model\r\n- **Traditional Software**: Customer implements software.\r\n- **Traditional Consulting**: Consultants perform implementation.\r\n- **Traditional AI**: AI answers questions.\r\n- **aegisOS**: AI completes implementations.\r\n\r\n`;

txt = txt.replace(/(###\s+Non-goals)/, philosophyAndModel + '$1');

const workforce = `##  Digital Workforce\r\nEvery Agent represents a Digital Employee.\r\n\r\nEvery Digital Employee has:\r\n- Identity\r\n- Role\r\n- Responsibilities\r\n- Skills\r\n- Memory\r\n- Knowledge\r\n- Permissions\r\n- Audit History\r\n- Performance Metrics\r\n- Lifecycle\r\n\r\n###  Implementation Project Hierarchy\r\nThe platform operates on the following conceptual execution hierarchy:\r\n1. **Implementation Project**\r\n2. **Digital Team**\r\n3. **Agent (Digital Employee)**\r\n4. **Skill**\r\n5. **Task**\r\n\r\n###  Implementation Templates\r\nImplementation Templates are prebuilt combinations of Agents, Skills, Workflows, Knowledge, and Memory designed for specific domains.\r\n\r\nExamples:\r\n- ERP Implementation\r\n- CRM Migration\r\n- Shopify Migration\r\n- AWS Infrastructure\r\n- Kubernetes Cluster\r\n- Salesforce Rollout\r\n- Microsoft 365 Deployment\r\n\r\n`;

txt = txt.replace(/(##\s+Architectural Principles)/, workforce + '$1');

txt = txt.replace(/(###\s+What is aegisOS[\s\S]*?)(?=###\s+Who it is for)/, `$1\r\n**Supported Domains:**\r\nSupported implementation domains include: ERP, CRM, HRMS, DevOps, Infrastructure, Cloud, Security, E-Commerce, Data Migration, and Enterprise Integration.\r\n\r\n`);

const newRoadmap = `##  Future Roadmap\r\n\r\n###  Phase 1\r\nERP\r\n\r\n###  Phase 2\r\nCRM, HRMS\r\n\r\n###  Phase 3\r\nCloud Infrastructure, DevOps\r\n\r\n###  Phase 4\r\nEnterprise Integration\r\n\r\n###  Phase 5\r\nUniversal Implementation Platform\r\n\r\n`;

txt = txt.replace(/##\s+Future Roadmap[\s\S]*?(?=##\s+Platform Capability Map)/, newRoadmap);

fs.writeFileSync('d:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.0.md', txt);
fs.unlinkSync(file);
console.log('Update complete.');
