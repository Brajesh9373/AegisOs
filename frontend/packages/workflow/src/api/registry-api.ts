import { WorkflowRegistry, WorkflowBase } from '../core/registry.js';

export class WorkflowRegistryAPI {
  constructor(private registry: WorkflowRegistry) {}

  public registerWorkflow(workflow: WorkflowBase): void {
    this.registry.register(workflow);
  }

  public getWorkflow(id: string): WorkflowBase {
    return this.registry.get(id);
  }

  public listWorkflows(): WorkflowBase[] {
    return this.registry.getAll();
  }
}
