import { WorkflowNode, WorkflowNodeType } from './nodes.js';

export interface HumanTaskDefinition extends WorkflowNode {
  type: WorkflowNodeType.HumanTask;
  assignee: string;
  formId?: string;
  timeoutSeconds?: number;
}
