import { EscalationTask } from './types';

export interface IEscalationRepository {
  create(task: Omit<EscalationTask, 'id' | 'createdAt' | 'updatedAt'>): Promise<EscalationTask>;
  findById(id: string): Promise<EscalationTask | null>;
  update(id: string, updates: Partial<EscalationTask>): Promise<void>;
  findPending(): Promise<EscalationTask[]>;
}
