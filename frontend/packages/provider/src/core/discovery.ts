import { ProviderRegistry, ProviderBase } from './registry.js';

export class ProviderDiscovery {
  constructor(private registry: ProviderRegistry) {}

  public discover(name: string): ProviderBase[] {
    return this.registry.getAll().filter((k: ProviderBase) => k.name === name);
  }
}
