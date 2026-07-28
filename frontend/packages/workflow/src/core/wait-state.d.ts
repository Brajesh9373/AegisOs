import { WorkflowNode, WorkflowNodeType } from './nodes.js';
export interface WaitStateDefinition extends WorkflowNode {
    type: WorkflowNodeType.WaitState;
    waitDurationSeconds?: number;
    waitUntilTime?: string;
}
