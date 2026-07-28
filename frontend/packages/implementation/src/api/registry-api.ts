import { ImplementationRegistry, ImplementationBase } from '../core/registry.js';

export class ImplementationRegistryAPI {
  constructor(private registry: ImplementationRegistry) {}

  public registerImplementation(item: ImplementationBase): void {
    this.registry.register(item);
  }

  public getImplementation(id: string): ImplementationBase {
    return this.registry.get(id);
  }

  public listImplementations(): ImplementationBase[] {
    return this.registry.getAll();
  }
}
