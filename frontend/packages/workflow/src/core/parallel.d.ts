import { WorkflowNode, WorkflowNodeType } from './nodes.js';
export interface ParallelBranchDefinition extends WorkflowNode {
    type: WorkflowNodeType.Parallel;
    branches: string[][];
}
