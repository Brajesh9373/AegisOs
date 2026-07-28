const fs = require('fs');
const oldFile = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.6.md';
let txt = fs.readFileSync(oldFile, 'utf8');

// 1. Version Bump
txt = txt.replace(/Version: 2\.6\.0/g, 'Version: 2.7.0');
txt = txt.replace(/#  aegisOS Platform Blueprint v2\.6/g, '#  aegisOS Platform Blueprint v2.7');

// 2. Add to Canonical Platform Definitions
const canonicalExperience = `###  Experience\r\nThe architectural capability enabling the platform to continuously learn from completed implementations. Experience is strictly distinct from Knowledge (factual domain data) and Memory (episodic state). Instead, Experience represents distilled, reusable implementation wisdom.\r\n\r\n`;
txt = txt.replace(/(##\s+Canonical Platform Definitions\r?\n\r?\n)/, `$1${canonicalExperience}`);

// 3. Add to Platform Capability Map (including interaction specifics)
const capabilityExperience = `###  Experience\r\n- **Purpose**: Continuously learn from completed implementations and store reusable implementation wisdom.\r\n- **Contains**: Lessons Learned, Best Practices, Optimization Patterns, Failure Recovery strategies, Implementation Strategies, Execution Statistics, and Successful Playbooks.\r\n- **Responsibilities**: Distilling raw execution telemetry and validation results into generalized, reusable strategies.\r\n- **Owner**: Platform AI.\r\n- **Consumers**: Planning Engine, Assessment Engine, Implementation Templates.\r\n- **Dependencies**: Depends on Audit, Evidence, and Memory from completed projects to mine insights.\r\n- **Lifecycle**: Mined from execution, Curated, Published to Experience Library, Applied to future plans.\r\n- **Interaction with Knowledge**: Knowledge stores facts (e.g., "What is a Kubernetes cluster?"). Experience stores operational wisdom (e.g., "Deploying Kubernetes on AWS in highly regulated sectors requires pre-configuring the transit gateway to avoid timeout failures").\r\n- **Interaction with Memory**: Memory is the episodic state of *this specific current project*. Experience is the aggregated wisdom across *all past completed projects*.\r\n- **Interaction with Templates**: Experience continuously refines Implementation Templates, dynamically injecting newly discovered best practices and failure recovery rules into standard template definitions.\r\n- **Future Evolution**: Autonomous refactoring of the platform's core Skills based on statistical failure rates identified in Experience.\r\n\r\n`;
txt = txt.replace(/(##\s+Platform Capability Map\r?\n\r?\n)/, `$1${capabilityExperience}`);

// 4. Add to Bounded Context Map
const boundedExperience = `###  Experience Context\r\n- **Purpose**: System of record for generalized implementation wisdom.\r\n- **Ownership**: Platform AI.\r\n- **Responsibilities**: Mining past executions for reusable patterns and serving them to the Planning Engine.\r\n- **Public interfaces**: \`queryPatterns\`, \`registerLesson\`.\r\n- **Upstream contexts**: Audit Context, Memory Context, Evidence Context.\r\n- **Downstream contexts**: Storage Context.\r\n- **Communication rules**: Asynchronous background mining; synchronous reads during Planning.\r\n- **Isolation rules**: Strictly isolated from active execution pipelines; operates purely as an offline analytical and serving layer.\r\n- **Shared kernel rules**: Shares \`Playbook\` and \`Lesson\` schemas.\r\n- **Context boundaries**: Stops at insight generation; it does not directly modify active workflows.\r\n\r\n`;
txt = txt.replace(/(##\s+Bounded Context Map\r?\n\r?\n)/, `$1${boundedExperience}`);

// 5. Add to Package Dependency Matrix (Table)
const packageExperience = `| \`@aegis/experience\` | \`contracts\`, \`storage\` | API | Planning, Templates | Platform AI | Logic | Reusable implementation wisdom |\r\n`;
txt = txt.replace(/(\| \`@aegis\/agents\`)/, `${packageExperience}$1`);

// 6. Add to the numeric list of packages
txt = txt.replace(/22\. \`@aegis\/evidence\`/, "22. `@aegis/evidence`\r\n23. `@aegis/experience`");

fs.writeFileSync('d:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.7.md', txt);
fs.unlinkSync(oldFile);
console.log('Update complete.');
