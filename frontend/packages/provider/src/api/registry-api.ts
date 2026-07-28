import { ProviderRegistry, ProviderBase } from '../core/registry.js';

export class ProviderRegistryAPI {
  constructor(private registry: ProviderRegistry) {}

  public registerProvider(item: ProviderBase): void {
    this.registry.register(item);
  }

  public getProvider(id: string): ProviderBase {
    return this.registry.get(id);
  }

  public listProviders(): ProviderBase[] {
    return this.registry.getAll();
  }
}
