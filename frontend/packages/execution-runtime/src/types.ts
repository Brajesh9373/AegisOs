export enum ExecutionState {
  Created = 'created',
  Scheduled = 'scheduled',
  Running = 'running',
  Waiting = 'waiting',
  Retrying = 'retrying',
  Paused = 'paused',
  Cancelled = 'cancelled',
  Failed = 'failed',
  Completed = 'completed',
}

export interface ExecutionContext {
  executionId: string;
  traceId: string;
  correlationId: string;
  state: ExecutionState;
  variables: Map<string, unknown>;
  startTime?: number;
  endTime?: number;
}

export interface ExecutionPolicy {
  maxRetries?: number;
  timeoutMs?: number;
  concurrencyLimit?: number;
  compensationEnabled?: boolean;
  rollbackEnabled?: boolean;
}

export interface ExecutionEvent {
  type: string;
  executionId: string;
  timestamp: number;
  payload?: unknown;
}
