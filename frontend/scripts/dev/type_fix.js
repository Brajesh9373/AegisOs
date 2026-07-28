const fs = require('fs');

function refactorFile(filePath, replacements) {
    if (fs.existsSync(filePath)) {
        let text = fs.readFileSync(filePath, 'utf8');
        replacements.forEach(([search, replace]) => {
            text = text.replace(search, replace);
        });
        fs.writeFileSync(filePath, text);
    }
}

// 1. Security
refactorFile('packages/security/src/index.ts', [
    [/claims: Record<string, unknown>;/g, 'claims: Record<string, string>;'],
    [/verifySignature\(payload: unknown, signature: string\)/g, 'verifySignature(payload: string, signature: string)'],
    [/evaluate\(attributes: Record<string, unknown>, required: Record<string, unknown>\)/g, 'evaluate(attributes: Record<string, string>, required: Record<string, string>)'],
    [/evaluate\(policy: unknown, context: unknown\)/g, 'evaluate(policy: Record<string, string>, context: IdentityContext)'],
    [/evaluateRiskLevel\(context: unknown\)/g, 'evaluateRiskLevel(context: IdentityContext)'],
    [/details: unknown;/g, 'details: Record<string, string>;'],
    [/getRisk\(ctx: unknown\)/g, 'getRisk(ctx: IdentityContext)']
]);

// 2. Manager Dashboard
refactorFile('packages/manager-dashboard/src/index.ts', [
    [/import \{ IdentityContext, SecurityEngine \} from "@aegisos\/security";/, 'import { IdentityContext, SecurityEngine } from "@aegisos/security";\nimport { DigitalEmployee, Task, AuditEvent } from "@aegisos/contracts";'],
    [/digitalEmployees: unknown\[\];/g, 'digitalEmployees: DigitalEmployee[];'],
    [/runningTasks: unknown\[\];/g, 'runningTasks: Task[];'],
    [/securityEvents: unknown\[\];/g, 'securityEvents: AuditEvent[];'],
    [/approvalsPending: unknown\[\];/g, 'approvalsPending: Task[];'],
    [/getEmployeeTimeline\(identity: IdentityContext, employeeId: string\): unknown\[\]/g, 'getEmployeeTimeline(identity: IdentityContext, employeeId: string): Task[]'],
    [/subscribeToEvents\(identity: IdentityContext, callback: \(event: unknown\) => void\)/g, 'subscribeToEvents(identity: IdentityContext, callback: (event: AuditEvent) => void)']
]);

// 3. Digital Employee Workspace
refactorFile('packages/digital-employee-workspace/src/index.ts', [
    [/import \{ IdentityContext, SecurityEngine \} from "@aegisos\/security";/, 'import { IdentityContext, SecurityEngine } from "@aegisos/security";\nimport { Task, MemorySnapshot, KnowledgeGraphNode, MemoryAsset, AuditEvent } from "@aegisos/contracts";'],
    [/inbox: unknown\[\];/g, 'inbox: Task[];'],
    [/assignedTasks: unknown\[\];/g, 'assignedTasks: Task[];'],
    [/currentContext: unknown;/g, 'currentContext: MemorySnapshot | null;'],
    [/knowledgeContext: unknown;/g, 'knowledgeContext: KnowledgeGraphNode[];'],
    [/memoryContext: unknown;/g, 'memoryContext: MemorySnapshot[];'],
    [/workspaceNotes: unknown\[\];/g, 'workspaceNotes: MemoryAsset[];'],
    [/calendar: unknown\[\];/g, 'calendar: Task[];'],
    [/notifications: unknown\[\];/g, 'notifications: AuditEvent[];'],
    [/approvals: unknown\[\];/g, 'approvals: Task[];'],
    [/learningQueue: unknown\[\];/g, 'learningQueue: Task[];'],
    [/deliverables: unknown\[\];/g, 'deliverables: MemoryAsset[];'],
    [/personalMetrics: unknown;/g, 'personalMetrics: Record<string, number>;'],
    [/budgetConsumption: unknown;/g, 'budgetConsumption: { limit: number, consumed: number };'],
    [/getExecutionHistory\(identity: IdentityContext\): unknown\[\]/g, 'getExecutionHistory(identity: IdentityContext): Task[]'],
    [/getEvidence\(identity: IdentityContext, taskId: string\): unknown\[\]/g, 'getEvidence(identity: IdentityContext, taskId: string): MemoryAsset[]'],
    [/updateContext\(identity: IdentityContext, updates: unknown\)/g, 'updateContext(identity: IdentityContext, updates: Record<string, string>)'],
    [/getTask\(identity: IdentityContext, taskId: string\): unknown \{/g, 'getTask(identity: IdentityContext, taskId: string): Task | null {'],
    [/updateTask\(identity: IdentityContext, taskId: string, updates: unknown\): unknown \{/g, 'updateTask(identity: IdentityContext, taskId: string, updates: Record<string, string>): Task | null {'],
    [/getWorkspaceContext\(identity: IdentityContext\): unknown \{/g, 'getWorkspaceContext(identity: IdentityContext): Record<string, string> {'],
    [/executeTask\(identity: IdentityContext, taskId: string\): unknown \{/g, 'executeTask(identity: IdentityContext, taskId: string): boolean {'],
    [/getHistory\(identity: IdentityContext\): unknown\[\] \{/g, 'getHistory(identity: IdentityContext): Task[] {'],
    [/getEvidence\(identity: IdentityContext, taskId: string\): unknown\[\] \{/g, 'getEvidence(identity: IdentityContext, taskId: string): MemoryAsset[] {']
]);

// 4. Knowledge Studio
refactorFile('packages/knowledge-studio/src/index.ts', [
    [/import \{ IdentityContext, SecurityEngine \} from "@aegisos\/security";/, 'import { IdentityContext, SecurityEngine } from "@aegisos/security";\nimport { KnowledgeGraphNode, Task, MemoryAsset, LedgerEntry, SecurityPolicy } from "@aegisos/contracts";'],
    [/knowledgeSources: unknown\[\];/g, 'knowledgeSources: KnowledgeGraphNode[];'],
    [/connectorManagement: unknown\[\];/g, 'connectorManagement: Record<string, string>[];'],
    [/knowledgeProcessingJobs: unknown\[\];/g, 'knowledgeProcessingJobs: Task[];'],
    [/knowledgeGraphExplorer: unknown;/g, 'knowledgeGraphExplorer: Record<string, string>;'],
    [/entityExplorer: unknown;/g, 'entityExplorer: Record<string, string>;'],
    [/relationshipExplorer: unknown;/g, 'relationshipExplorer: Record<string, string>;'],
    [/classification: unknown;/g, 'classification: Record<string, string>;'],
    [/versionHistory: unknown\[\];/g, 'versionHistory: LedgerEntry[];'],
    [/knowledgeDiff: unknown;/g, 'knowledgeDiff: Record<string, string>;'],
    [/knowledgeSearch: unknown;/g, 'knowledgeSearch: Record<string, string>;'],
    [/knowledgeLineage: unknown;/g, 'knowledgeLineage: LedgerEntry[];'],
    [/knowledgeProvenance: unknown;/g, 'knowledgeProvenance: Record<string, string>;'],
    [/knowledgePolicies: unknown\[\];/g, 'knowledgePolicies: SecurityPolicy[];'],
    [/knowledgeACLReview: unknown\[\];/g, 'knowledgeACLReview: Task[];'],
    [/connectorSyncStatus: unknown\[\];/g, 'connectorSyncStatus: Record<string, string>[];'],
    [/failedImports: unknown\[\];/g, 'failedImports: Task[];'],
    [/pendingReviews: unknown\[\];/g, 'pendingReviews: Task[];'],
    [/humanApprovalQueue: unknown\[\];/g, 'humanApprovalQueue: Task[];'],
    [/getLineage\(identity: IdentityContext, nodeId: string\): unknown/g, 'getLineage(identity: IdentityContext, nodeId: string): LedgerEntry[]'],
    [/getPendingReviews\(identity: IdentityContext\): unknown\[\]/g, 'getPendingReviews(identity: IdentityContext): Task[]'],
    [/explore\(identity: IdentityContext, query: string\): unknown/g, 'explore(identity: IdentityContext, query: string): KnowledgeGraphNode[]']
]);

// 5. Connector Framework Legacy Adapter
refactorFile('packages/connector-framework/src/adapters/legacy.ts', [
    [/payload: unknown/g, 'payload: Record<string, string>']
]);

// 6. Config loader
refactorFile('packages/config/src/core/loader.ts', [
    [/environment: process.env.NODE_ENV as unknown/g, 'environment: process.env.NODE_ENV as string']
]);
