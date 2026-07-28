export enum WorkflowState {
  Pending = 'pending',
  Running = 'running',
  WaitingForApproval = 'waiting_approval',
  Compensating = 'compensating',
  Completed = 'completed',
  Failed = 'failed',
}

export interface WorkflowInstanceModel {
  id: string;
  definitionId: string;
  state: WorkflowState;
  contextData: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowPersistenceContract {
  saveInstance(instance: WorkflowInstanceModel): Promise<void>;
  loadInstance(id: string): Promise<WorkflowInstanceModel | null>;
}

export interface WorkflowMetricsContract {
  recordNodeExecution(nodeId: string, durationMs: number, success: boolean): void;
  recordWorkflowCompletion(workflowId: string, durationMs: number): void;
}

export interface NodeDefinition {
  id: string;
  type: string;
  config: Record<string, unknown>;
}

export interface EdgeDefinition {
  source: string;
  target: string;
  condition?: string;
}

export interface WorkflowDefinition {
  id: string;
  nodes: NodeDefinition[];
  edges: EdgeDefinition[];
}
