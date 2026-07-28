import { WorkflowNode, WorkflowNodeType } from './nodes.js';
export interface SequentialFlowDefinition extends WorkflowNode {
    type: WorkflowNodeType.Sequential;
    steps: string[];
}
