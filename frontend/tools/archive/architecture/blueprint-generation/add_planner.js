const fs = require('fs');
const file = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.0.md';
let txt = fs.readFileSync(file, 'utf8');

const plannerCanonical = `###  Planner\r\nThe strategic compilation engine. It converts abstract Business Goals into deterministic implementation plans, strictly existing above the Workflow execution layer.\r\n\r\n`;

const plannerCapability = `###  Planner\r\n- **Purpose**: Convert Business Goals into executable implementation plans.\r\n- **Responsibilities**: Decomposing abstract objectives into deterministic Directed Acyclic Graphs (DAGs), mapping required Skills, and allocating Digital Teams.\r\n- **Inputs**: Business Goal definitions, feasibility reports, target environment state.\r\n- **Outputs**: Fully constructed Workflow definitions, Agent assignments, and resource requirement manifests.\r\n- **Dependencies**: Depends on the Knowledge Base for historical template retrieval; strictly upstream of Workflow.\r\n- **Boundaries**: The Planner never executes tasks. It is strictly a compilation and generation layer. Once a plan is compiled, it is handed off to the Workflow engine.\r\n- **Future Evolution**: Autonomous re-planning during active execution to route around unexpected external system outages.\r\n\r\n`;

// Insert into Canonical Platform Definitions before ###  Workflow
txt = txt.replace(/(###\s+Workflow\r?\nThe stateful DAG)/, plannerCanonical + '$1');

// Insert into Platform Capability Map before ###  Workflow\n\n\n- **Purpose**: Stateful DAG
txt = txt.replace(/(###\s+Workflow[\r\n]+-\s\*\*Purpose\*\*: Stateful DAG)/, plannerCapability + '$1');

fs.writeFileSync(file, txt);
console.log('Planner module added.');
