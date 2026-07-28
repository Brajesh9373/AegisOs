const fs = require('fs');
const file = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.0.md';
let txt = fs.readFileSync(file, 'utf8');

// 1. Version bumps
txt = txt.replace('Version: 2.0.0', 'Version: 2.1.0');
txt = txt.replace('#  aegisOS Platform Blueprint v2.0', '#  aegisOS Platform Blueprint v2.1');

// 2. Hierarchy in Digital Workforce
const oldProjectHierarchy = `###  Implementation Project Hierarchy\r\nThe platform operates on the following conceptual execution hierarchy:\r\n1. **Implementation Project**\r\n2. **Digital Team**\r\n3. **Agent (Digital Employee)**\r\n4. **Skill**\r\n5. **Task**`;

const newProjectHierarchy = `###  Implementation Project Hierarchy\r\nThe platform operates on the following conceptual execution hierarchy:\r\n1. **Implementation Project**\r\n2. **Digital Team**\r\n3. **Workflow**\r\n4. **Agent (Digital Employee)**\r\n5. **Skill**\r\n6. **Task**\r\n7. **Action**`;

txt = txt.replace(/###\s+Implementation Project Hierarchy[\s\S]*?(?=###\s+Implementation Templates)/, newProjectHierarchy + '\n\n');

// 3. Hierarchy in Department section
const oldDeptHierarchy = `The complete topological hierarchy is now explicitly defined as:\r\n1. Organization\r\n2. Department\r\n3. Workspace\r\n4. Implementation Project\r\n5. Digital Team\r\n6. Agent\r\n7. Skill\r\n8. Task`;

const newDeptHierarchy = `The complete topological hierarchy is now explicitly defined as:\r\n1. Organization\r\n2. Department\r\n3. Workspace\r\n4. Business Goal\r\n5. Implementation Project\r\n6. Digital Team\r\n7. Workflow\r\n8. Agent\r\n9. Skill\r\n10. Task\r\n11. Action`;

txt = txt.replace(/The complete topological hierarchy is now explicitly defined as:[\s\S]*?(?=###\s+Responsibilities)/, newDeptHierarchy + '\n\n');

// 4. State machine consistency
const oldAgentState = `- **Initial state**: \`IDLE\`\r\n- **Intermediate states**: \`THINKING\`, \`ACTING\`, \`OBSERVING\`\r\n- **Failure states**: \`ERROR\`, \`HALTED\`\r\n- **Recovery states**: \`REPLANNING\`\r\n- **Terminal states**: \`GOAL_MET\`, \`GOAL_FAILED\`\r\n- **Allowed transitions**: \`THINKING -> ACTING\`, \`ACTING -> OBSERVING\`\r\n- **Forbidden transitions**: \`IDLE -> ACTING\` \\(Must think first\\)`;

const newAgentState = `- **Initial state**: \`DRAFT\`\r\n- **Intermediate states**: \`CREATED\`, \`ASSIGNED\`, \`TRAINING\`, \`READY\`, \`EXECUTING\`, \`WAITING\`, \`REVIEW\`\r\n- **Failure states**: \`HALTED\`\r\n- **Recovery states**: \`TRAINING\`, \`REVIEW\`\r\n- **Terminal states**: \`COMPLETED\`, \`RETIRED\`\r\n- **Allowed transitions**: \`READY -> EXECUTING\`, \`EXECUTING -> WAITING\`, \`WAITING -> EXECUTING\`, \`EXECUTING -> REVIEW\`\r\n- **Forbidden transitions**: \`RETIRED -> READY\`, \`DRAFT -> EXECUTING\``;

txt = txt.replace(/- \*\*Initial state\*\*: `IDLE`[\s\S]*?\(Must think first\)/, newAgentState);

// Rename file to v2.1
const newFile = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.1.md';
fs.writeFileSync(newFile, txt);
fs.unlinkSync(file);

console.log('Consistency validations applied. Saved as v2.1.');
