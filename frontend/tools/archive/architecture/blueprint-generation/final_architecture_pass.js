const fs = require('fs');
const oldFile = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.11.md';
let txt = fs.readFileSync(oldFile, 'utf8');

// Version bump to 3.0 (final architecture pass)
txt = txt.replace(/Version: 2\.11\.0/g, 'Version: 3.0.0');
txt = txt.replace(/#  aegisOS Platform Blueprint v2\.11/g, '#  aegisOS Platform Blueprint v3.0');

// 1. Implementation Engine, Validation Engine, Deployment Engine
const newEnginesCanonical = `###  Implementation Engine\r\nThe core orchestrator executing every Implementation Project regardless of technology stack (ERP, CRM, HRMS, E-Commerce, Cloud, Infrastructure, Networking, Security, Identity, DevOps, Data Migration, Database Migration, Application Deployment, Platform Modernization). It coordinates Digital Teams, executes Implementation Graphs, manages execution phases, tracks execution state, and coordinates rollbacks, validation, evidence generation, approvals, and completion.\r\n\r\n###  Validation Engine\r\nThe authoritative evaluator responsible for Configuration Validation, Business Validation, Compliance Validation, Security Validation, Performance Validation, Smoke Testing, Regression Testing, Dependency Validation, and Health Validation. It produces Validation Reports, Evidence, Success Status, and Approval Inputs.\r\n\r\n###  Deployment Engine\r\nThe executor for Release Coordination, Promotion, Deployment, Rollback, Blue-Green, Canary, Feature Flag Activation, Version Promotion, and Environment Synchronization. It consumes Implementation and Validation Results, producing Deployment Reports and Evidence.\r\n\r\n`;
txt = txt.replace(/(###\s+Discovery Engine\r?\n\*\*Purpose\*\*: Automatically discover)/, newEnginesCanonical + '$1');

// Update Capability Map with the new engines
const newEnginesCapability = `###  Implementation Engine\r\n- **Purpose**: Orchestrate execution across any technology stack.\r\n- **Responsibilities**: Coordinate Digital Teams, execute Implementation Graphs, manage execution state, coordinate rollbacks, validation, evidence, approvals, and completion.\r\n\r\n###  Validation Engine\r\n- **Purpose**: Authoritative evidentiary evaluator.\r\n- **Responsibilities**: Configuration, Business, Compliance, Security, Performance, Smoke, Regression, Dependency, and Health Validation.\r\n- **Outputs**: Validation Reports, Evidence, Success Status, Approval Inputs.\r\n\r\n###  Deployment Engine\r\n- **Purpose**: Live environment transition coordinator.\r\n- **Responsibilities**: Release Coordination, Promotion, Deployment, Rollback, Blue-Green, Canary, Feature Flag Activation, Version Promotion, Environment Synchronization.\r\n- **Consumes**: Implementation Results, Validation Results.\r\n- **Outputs**: Deployment Reports, Deployment Evidence.\r\n\r\n`;
txt = txt.replace(/(###\s+Discovery Engine\r?\n- \*\*Purpose\*\*: Automatically discover)/, newEnginesCapability + '$1');

// 2. Expand Digital Teams with Roles
const oldTeam = /###  Digital Team\r?\n- \*\*Responsibility\*\*: An autonomous collective of specialized Agents assigned to execute specific Workflow branches\./;
const newTeam = `###  Digital Team\r\n- **Responsibility**: An autonomous collective of specialized Agents assigned to execute specific Workflow branches. Digital Teams consist of specialized Digital Employees fulfilling explicit roles (e.g., Program Manager, Project Manager, Solution Architect, Discovery Specialist, Assessment Specialist, Planner, Implementation Engineer, Migration Engineer, Validation Engineer, Security Engineer, QA Engineer, Documentation Engineer, Rollback Engineer, Knowledge Engineer). Every role is structurally implemented by one or more Agents.`;
txt = txt.replace(oldTeam, newTeam);

// 3. Clarify Agent Responsibility Model
const oldAgentCap = /###  Agent\r?\n- \*\*Purpose\*\*: Autonomous decision execution\./;
const newAgentCap = `###  Agent Responsibility Model\r\nThe platform enforces a strict dichotomy between intelligence and execution:\r\n- **Agent**: Reasons, Plans, Coordinates, Owns Memory, Owns Knowledge, Uses Skills.\r\n- **Skill**: Performs execution only. Skills never perform reasoning. Skills remain stateless, reusable execution capabilities.\r\n\r\n###  Agent\r\n- **Purpose**: Autonomous decision execution.`;
txt = txt.replace(oldAgentCap, newAgentCap);

// 4. Update Environment explicit definition
const oldEnv = /###  Environment\r?\nFirst-class platform entity acting as the execution target for Implementation Projects\. Represents Source Environments \(where data is pulled from\) and Target Environments \(where changes are applied\)\.[\s\S]*?(?=###  Asset Inventory)/;
const newEnv = `###  Environment\r\nFirst-class platform entity acting as the execution boundary for Implementation Projects. Represents Source Environments (where data is pulled from) and Target Environments (where changes are applied).\r\n- **Examples**: Development, Testing, QA, Sandbox, Production, AWS Account, Azure Subscription, GCP Project, Kubernetes Cluster, VM Infrastructure, On-Premise Datacenter.\r\n- **Ownership**: The Environment structurally owns Assets, Topology, Endpoints, Connections, Configuration, Variables, Credential References (never secrets), Policies, and Execution Boundaries.\r\n- **Participation**: Actively participates in Discovery, Assessment, Planning, Implementation, Validation, Deployment, and Rollback.\r\n\r\n`;
txt = txt.replace(oldEnv, newEnv);

fs.writeFileSync('d:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v3.0.md', txt);
fs.unlinkSync(oldFile);
console.log('Update complete.');
