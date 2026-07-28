import { MemoryRegistry, MemoryBase } from './registry.js';

export class MemoryRegistryAPI {
  constructor(private registry: MemoryRegistry) {}

  public getMemory(id: string): MemoryBase {
    return this.registry.get(id);
  }

  public registerMemory(item: MemoryBase): void {
    this.registry.register(item);
  }

  public listMemory(): MemoryBase[] {
    return this.registry.getAll();
  }
}
