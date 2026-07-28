export enum WorkflowEventType {
  Started = 'workflow.started',
  Completed = 'workflow.completed',
  Failed = 'workflow.failed',
  NodeEntered = 'workflow.node.entered',
  NodeExited = 'workflow.node.exited',
}

export interface WorkflowEvent {
  type: WorkflowEventType;
  workflowId: string;
  timestamp: Date;
  payload?: Record<string, unknown>;
}
