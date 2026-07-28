import { BaseEntity } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';

// For foundation purposes we'll define a MemoryBase representation
export interface MemoryBase extends BaseEntity {
  name: string;
  version: string;
  description: string;
  sourceType: string;
}

export class MemoryNotFoundError extends PlatformError {
  constructor(id: string) {
    super(`Memory with ID ${id} not found`);
  }
}

export class MemoryRegistry {
  private items = new Map<string, MemoryBase>();

  public register(item: MemoryBase): void {
    this.items.set(item.id, item);
  }

  public get(id: string): MemoryBase {
    const item = this.items.get(id);
    if (!item) {
      throw new MemoryNotFoundError(id);
    }
    return item;
  }

  public getAll(): MemoryBase[] {
    return Array.from(this.items.values());
  }

  public remove(id: string): void {
    this.items.delete(id);
  }
}
