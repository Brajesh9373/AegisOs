import { OrchestratorRegistry, OrchestratorBase } from '../core/registry.js';

export class OrchestratorRegistryAPI {
  constructor(private registry: OrchestratorRegistry) {}

  public registerOrchestrator(item: OrchestratorBase): void {
    this.registry.register(item);
  }

  public getOrchestrator(id: string): OrchestratorBase {
    return this.registry.get(id);
  }

  public listOrchestrators(): OrchestratorBase[] {
    return this.registry.getAll();
  }
}
