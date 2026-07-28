import { DigitalEmployee } from '@aegisos/contracts';
import { AgentRegistry } from '../core/registry';

export class AgentDiscovery {
  constructor(private registry: AgentRegistry) {}

  public findByRole(role: string): DigitalEmployee[] {
    return this.registry.getAll().filter((agent) => agent.role === role);
  }

  public findByDepartment(department: string): DigitalEmployee[] {
    return this.registry.getAll().filter((agent) => agent.department === department);
  }

  public findIdleWorkers(): DigitalEmployee[] {
    return this.registry
      .getAll()
      .filter((agent) => agent.status === 'Idle' && agent.role === 'Worker');
  }
}
