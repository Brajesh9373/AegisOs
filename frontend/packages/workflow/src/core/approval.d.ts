import { WorkflowNode, WorkflowNodeType } from './nodes.js';
export interface ApprovalStepDefinition extends WorkflowNode {
    type: WorkflowNodeType.Approval;
    approvers: string[];
    timeoutSeconds?: number;
}
