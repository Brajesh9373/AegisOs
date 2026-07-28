const fs = require('fs');
const oldFile = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.9.md';
let txt = fs.readFileSync(oldFile, 'utf8');

// 1. Version Bump
txt = txt.replace(/Version: 2\.9\.0/g, 'Version: 2.10.0');
txt = txt.replace(/#  aegisOS Platform Blueprint v2\.9/g, '#  aegisOS Platform Blueprint v2.10');

// 2. Add to Implementation Project
const oldImplProject = /###  Implementation Project\r?\n- \*\*Responsibility\*\*: Translates the Program into a structured timeline of deliverables, managing global project constraints, budgets, and the allocation of Digital Teams\. Execution halts iteratively until the explicit Success Criteria defined by the Business Outcome are achieved\./g;
const newImplProject = `###  Implementation Project\r\n- **Responsibility**: Translates the Program into a structured timeline of deliverables, managing global project constraints, budgets, and the allocation of Digital Teams. Execution halts iteratively until the explicit Success Criteria defined by the Business Outcome are achieved. The Project structurally manages the Timeline—tracking Milestones, ETA, Deadlines, Critical Path, Dependencies, Execution Progress, Delays, and Forecasts. Agents execute the work; the Timeline strictly tracks it.`;
txt = txt.replace(oldImplProject, newImplProject);

// 3. Add to Planning Engine
const oldPlanningEngineCap = /###  Planning Engine\r?\n- \*\*Purpose\*\*: Convert Business Goals into executable implementation plans\.\r?\n- \*\*Responsibilities\*\*: Execution, Timeline, Dependency, Rollback, Approval, Resource Planning, Digital Team Assignment\./;
const newPlanningEngineCap = `###  Planning Engine\r\n- **Purpose**: Convert Business Goals into executable implementation plans.\r\n- **Responsibilities**: Execution, Dependency, Rollback, Approval, Resource Planning, Digital Team Assignment, and structural Timeline Management (calculating initial ETAs, Deadlines, and Critical Paths).`;
txt = txt.replace(oldPlanningEngineCap, newPlanningEngineCap);

// 4. Add to Workflow
const oldWorkflowCap = /###  Workflow\r?\n- \*\*Purpose\*\*: Stateful DAG orchestration parameterized by the precise Completion Rules and Rollback Requirements defined in the Business Outcome's Success Criteria\./;
const newWorkflowCap = `###  Workflow\r\n- **Purpose**: Stateful DAG orchestration parameterized by the precise Completion Rules and Rollback Requirements defined in the Business Outcome's Success Criteria. Constantly emits execution progress to update the structural Timeline, recalculating delays and forecasts in real-time.`;
txt = txt.replace(oldWorkflowCap, newWorkflowCap);

// 5. Add Timeline Management to Platform Capability Map
const capabilityTimeline = `###  Timeline Management\r\n- **Purpose**: Track implementation progress structurally, entirely decoupled from core execution mechanics.\r\n- **Responsibilities**: Managing Milestones, ETA, Deadlines, Critical Path, Dependencies, Execution Progress, Delays, and Forecasts.\r\n- **Interaction**: Agents execute work; the Timeline structurally tracks work without interfering with Agent logic.\r\n\r\n`;
txt = txt.replace(/(##\s+Platform Capability Map\r?\n\r?\n)/, `$1${capabilityTimeline}`);

// 6. Add to Future Modules
const oldFutureModules = /- Validation/;
const newFutureModules = `- Validation\r\n- Timeline Management`;
txt = txt.replace(oldFutureModules, newFutureModules);

fs.writeFileSync('d:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.10.md', txt);
fs.unlinkSync(oldFile);
console.log('Update complete.');
