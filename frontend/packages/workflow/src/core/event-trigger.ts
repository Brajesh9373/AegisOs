import { WorkflowNode, WorkflowNodeType } from './nodes.js';

export interface EventTriggerDefinition extends WorkflowNode {
  type: WorkflowNodeType.EventTrigger;
  eventType: string;
  eventFilter?: Record<string, unknown>;
}
