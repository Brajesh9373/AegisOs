import { WorkflowNode, WorkflowNodeType } from './nodes.js';
export interface ConditionalBranchDefinition extends WorkflowNode {
    type: WorkflowNodeType.Conditional;
    conditions: Array<{
        expression: string;
        next: string;
    }>;
    defaultNext?: string;
}
