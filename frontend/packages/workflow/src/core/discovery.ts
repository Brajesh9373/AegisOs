import { WorkflowRegistry, WorkflowBase } from './registry.js';

export class WorkflowDiscovery {
  constructor(private registry: WorkflowRegistry) {}

  public findByName(name: string): WorkflowBase[] {
    return this.registry.getAll().filter((k) => k.name === name);
  }
}
