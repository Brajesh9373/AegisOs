import { WorkflowNode, WorkflowNodeType } from './nodes.js';
export interface ScheduleTriggerDefinition extends WorkflowNode {
    type: WorkflowNodeType.ScheduleTrigger;
    cronExpression: string;
    timezone?: string;
}
