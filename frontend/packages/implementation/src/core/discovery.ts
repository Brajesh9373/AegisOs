import { ImplementationRegistry, ImplementationBase } from './registry.js';

export class ImplementationDiscovery {
  constructor(private registry: ImplementationRegistry) {}

  public discover(name: string): ImplementationBase[] {
    return this.registry.getAll().filter((k: ImplementationBase) => k.name === name);
  }
}
