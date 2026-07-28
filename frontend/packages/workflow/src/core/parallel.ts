import { WorkflowNode, WorkflowNodeType } from './nodes.js';

export interface ParallelBranchDefinition extends WorkflowNode {
  type: WorkflowNodeType.Parallel;
  branches: string[][]; // Array of paths, each path is an array of node IDs
}
