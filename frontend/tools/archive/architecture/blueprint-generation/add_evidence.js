const fs = require('fs');
const oldFile = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.5.md';
let txt = fs.readFileSync(oldFile, 'utf8');

// 1. Version Bump
txt = txt.replace(/Version: 2\.5\.0/g, 'Version: 2.6.0');
txt = txt.replace(/#  aegisOS Platform Blueprint v2\.5/g, '#  aegisOS Platform Blueprint v2.6');

// 2. Add to Canonical Platform Definitions
const canonicalEvidence = `###  Evidence\r\nEvery implementation step produces verifiable, immutable proof of work. While the Audit module records *that* an action occurred, Evidence captures the substantive *result* and *context* (e.g., screenshots, CLI outputs) of that action.\r\n\r\n`;
txt = txt.replace(/(##\s+Canonical Platform Definitions\r?\n\r?\n)/, `$1${canonicalEvidence}`);

// 3. Add to Platform Capability Map (including Execution Flow Integration)
const capabilityEvidence = `###  Evidence\r\n- **Purpose**: Ensure every implementation step produces verifiable proof of work.\r\n- **Examples**: Screenshots, API Responses, CLI Outputs, Terraform Plans, Deployment Logs, Audit Logs, Validation Reports, Compliance Reports, Test Reports, Execution Reports.\r\n- **Responsibilities**: Cryptographically binding execution outputs to their generating task and storing them immutably for external review.\r\n- **Owner**: Platform Governance.\r\n- **Consumers**: Approval Gates, Validation Engine, Customers, External Auditors.\r\n- **Dependencies**: Depends on Task and Agent contexts for generation; depends on Storage for persistence.\r\n- **Storage**: Persisted indefinitely in WORM (Write Once, Read Many) compliant cold storage.\r\n- **Lifecycle**: Generated, Cryptographically Signed, Stored, Reviewed, Archived.\r\n- **Execution Flow Integration**: Generated continuously during the Execution phase. Approval Gates halt workflows until human operators review the Evidence. Post-execution, the Validation phase consumes Evidence to certify the Business Outcome.\r\n- **Future Evolution**: Automated visual QA analysis of Evidence screenshots by secondary verifier models.\r\n\r\n`;
txt = txt.replace(/(##\s+Platform Capability Map\r?\n\r?\n)/, `$1${capabilityEvidence}`);

// 4. Add to Bounded Context Map
const boundedEvidence = `###  Evidence Context\r\n- **Purpose**: System of record for verifiable proof of work.\r\n- **Ownership**: Platform Governance.\r\n- **Responsibilities**: Aggregating, signing, and serving implementation artifacts.\r\n- **Public interfaces**: \`attachEvidence\`, \`retrieveEvidencePackage\`.\r\n- **Upstream contexts**: Task Context, Agent Context.\r\n- **Downstream contexts**: Storage Context.\r\n- **Communication rules**: Asynchronous fire-and-forget generation; synchronous retrieval for Approval Gates.\r\n- **Isolation rules**: Complements but strictly operates independently of the Audit Context (Audit tracks the transaction; Evidence stores the payload).\r\n- **Shared kernel rules**: Shares \`EvidencePackage\` types.\r\n- **Context boundaries**: Never parses or acts upon the Evidence; strictly acts as an immutable custodian.\r\n\r\n`;
txt = txt.replace(/(##\s+Bounded Context Map\r?\n\r?\n)/, `$1${boundedEvidence}`);

// 5. Add to Package Dependency Matrix (Table)
const packageEvidence = `| \`@aegis/evidence\` | \`contracts\`, \`storage\` | API | Guardian, Approval Gates | Platform Governance | Infra | Immutable proof of work |\r\n`;
txt = txt.replace(/(\| \`@aegis\/audit\`)/, `${packageEvidence}$1`);

// 6. Add to the numeric list of packages
txt = txt.replace(/21\. \`@aegis\/assets\`/, "21. `@aegis/assets`\r\n22. `@aegis/evidence`");

fs.writeFileSync('d:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.6.md', txt);
fs.unlinkSync(oldFile);
console.log('Update complete.');
