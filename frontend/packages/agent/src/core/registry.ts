import { DigitalEmployee } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';

export class AgentNotFoundError extends PlatformError {
  constructor(id: string) {
    super(`Agent with ID ${id} not found`);
  }
}

export class AgentRegistry {
  private agents = new Map<string, DigitalEmployee>();

  public register(agent: DigitalEmployee): void {
    this.agents.set(agent.id, agent);
  }

  public get(id: string): DigitalEmployee {
    const agent = this.agents.get(id);
    if (!agent) {
      throw new AgentNotFoundError(id);
    }
    return agent;
  }

  public getAll(): DigitalEmployee[] {
    return Array.from(this.agents.values());
  }

  public remove(id: string): void {
    this.agents.delete(id);
  }
}
