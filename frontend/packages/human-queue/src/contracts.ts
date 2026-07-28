import { EscalationTask, EscalationResult } from './types';

export interface IHumanQueueService {
  escalate(context: string, confidence: number): Promise<EscalationTask>;
  assignTask(taskId: string, userId: string): Promise<void>;
  resolveTask(taskId: string, resolution: string): Promise<EscalationResult>;
  getPendingTasks(): Promise<EscalationTask[]>;
}
