export enum TeamState {
  Forming = 'forming',
  Collaborating = 'collaborating',
  Escalated = 'escalated',
  Completed = 'completed',
  Failed = 'failed',
}

export interface TaskModel {
  taskId: string;
  payload: unknown;
  assignedTo?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
}

export interface TeamMetrics {
  tasksDistributed: number;
  tasksCompleted: number;
  escalationsCount: number;
  conflictsResolved: number;
}

export interface SupervisorPolicy {
  maxEscalations: number;
  autoResolveConflicts: boolean;
  delegationStrategy: 'round-robin' | 'skill-based';
}

export interface SharedMemoryLayer {
  get(key: string): unknown;
  set(key: string, value: unknown): void;
}

export interface SharedKnowledgeLayer {
  query(domain: string, params: unknown): Promise<unknown>;
}
