import { WorkflowBase } from './registry.js';

export class WorkflowFactory {
  public createWorkflow(id: string, name: string): WorkflowBase {
    return {
      id,
      name,
      version: '1.0.0',
      description: 'Auto-generated workflow',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  }
}
