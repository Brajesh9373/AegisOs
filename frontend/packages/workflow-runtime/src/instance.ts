import { WorkflowInstanceModel, WorkflowState } from './types.js';

export class WorkflowInstance {
  private model: WorkflowInstanceModel;

  constructor(definitionId: string) {
    this.model = {
      id: `wf-inst-${Math.random().toString(36).substring(7)}`,
      definitionId,
      state: WorkflowState.Pending,
      contextData: {},
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  }

  public getModel(): WorkflowInstanceModel {
    return this.model;
  }

  public updateState(newState: WorkflowState): void {
    this.model.state = newState;
    this.model.updatedAt = new Date().toISOString();
  }

  public updateContext(key: string, value: unknown): void {
    this.model.contextData[key] = value;
    this.model.updatedAt = new Date().toISOString();
  }
}
