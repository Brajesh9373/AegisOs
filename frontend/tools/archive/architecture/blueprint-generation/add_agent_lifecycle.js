const fs = require('fs');
const file = 'd:/experiments/aegisOS/.aegis/core/aegisOS-Platform-Blueprint-v2.0.md';
let txt = fs.readFileSync(file, 'utf8');

const agentLifecycle = `###  Agent\r\nThe autonomous decision-making actor within the system. It evaluates goals, reasons over context, selects appropriate tools/skills, and generates actions within the secure boundaries enforced by the Guardian.\r\n\r\n####  Agent Lifecycle\r\nThe structural state machine governing the existence and operational capacity of an Agent:\r\n\r\n- **Draft**: The preliminary state where the Agent's identity, role, and capabilities are being configured structurally. Execution is physically impossible.\r\n- **Created**: Configuration is validated and locked. The Agent identity is registered within the platform, awaiting assignment to a Digital Team.\r\n- **Assigned**: The Agent is structurally bound to a Digital Team and a specific Implementation Project, inheriting target environment contexts.\r\n- **Training**: The phase where the Agent ingests domain-specific Knowledge Bases, calibrates memory schemas, and validates its assigned Skills via the testing sandbox.\r\n- **Ready**: The Agent is fully calibrated, context-aware, and idle. It is securely listening for Workflow dispatches.\r\n- **Executing**: The active state where the Agent evaluates tasks, invokes Skills, and mutates external states under the absolute oversight of the Guardian.\r\n- **Waiting**: The blocked state where the Agent halts autonomous evaluation, pending an asynchronous external event (e.g., an API callback or a timer).\r\n- **Review**: The paused state triggered by an Approval Gate or Escalation. Execution yields context to a Human Operator pending manual cryptographic validation.\r\n- **Completed**: The terminal success state. The Agent has fulfilled its Workflow objectives. Memory is committed to long-term storage, and the execution loop terminates.\r\n- **Retired**: The permanent deactivation state. The Agent's cryptographic identity is revoked, preventing any future execution, while its Audit History is preserved indefinitely for compliance.\r\n`;

const oldAgent = `###  Agent\r\nThe autonomous decision-making actor within the system. It evaluates goals, reasons over context, selects appropriate tools/skills, and generates actions within the secure boundaries enforced by the Guardian.\r\n`;

// Since line endings can be \r\n or \n, replace via regex
txt = txt.replace(/###\s+Agent[\s\S]*?(?=###\s+Knowledge)/, agentLifecycle + '\n');

fs.writeFileSync(file, txt);
console.log('Agent lifecycle added.');
