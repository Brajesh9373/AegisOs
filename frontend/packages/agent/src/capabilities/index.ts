import { PlatformError } from '@aegisos/shared';

export class CapabilityNotFoundError extends PlatformError {
  constructor(id: string) {
    super(`Capability with ID ${id} not found`);
  }
}

export class AgentCapabilityRegistry {
  private capabilities = new Map<string, string[]>();

  public registerCapability(agentId: string, capabilityId: string): void {
    const caps = this.capabilities.get(agentId) || [];
    if (!caps.includes(capabilityId)) {
      caps.push(capabilityId);
      this.capabilities.set(agentId, caps);
    }
  }

  public getCapabilities(agentId: string): string[] {
    return this.capabilities.get(agentId) || [];
  }

  public hasCapability(agentId: string, capabilityId: string): boolean {
    const caps = this.capabilities.get(agentId) || [];
    return caps.includes(capabilityId);
  }
}
