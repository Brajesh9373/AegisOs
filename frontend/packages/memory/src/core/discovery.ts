import { MemoryRegistry, MemoryBase } from './registry.js';

export class MemoryDiscovery {
  constructor(private registry: MemoryRegistry) {}

  public findByName(name: string): MemoryBase[] {
    return this.registry.getAll().filter((k) => k.name === name);
  }

  public findByType(type: string): MemoryBase[] {
    const result: MemoryBase[] = [];
    for (const k of this.registry.getAll()) {
      if (k.sourceType === type) {
        result.push(k);
      }
    }
    return result;
  }
}
