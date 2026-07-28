import { WorkflowNode, WorkflowNodeType } from './nodes.js';

export interface SwitchDefinition extends WorkflowNode {
  type: WorkflowNodeType.Switch;
  cases: Array<{
    value: string | number | boolean;
    nextNode: string;
  }>;
  defaultNode: string;
}
