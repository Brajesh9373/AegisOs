import { WorkflowNode, WorkflowNodeType } from './nodes.js';
export interface LoopDefinition extends WorkflowNode {
    type: WorkflowNodeType.Loop;
    loopCondition: string;
    loopBody: string;
    maxIterations?: number;
}
