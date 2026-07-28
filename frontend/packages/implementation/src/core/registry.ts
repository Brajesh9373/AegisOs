import { BaseEntity } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';

export interface ImplementationBase extends BaseEntity {
  name: string;
  version: string;
  description: string;
}

export class ImplementationNotFoundError extends PlatformError {
  constructor(id: string) {
    super(`Implementation with ID ${id} not found`);
  }
}

export class ImplementationRegistry {
  private items = new Map<string, ImplementationBase>();

  public register(item: ImplementationBase): void {
    this.items.set(item.id, item);
  }

  public get(id: string): ImplementationBase {
    const item = this.items.get(id);
    if (!item) {
      throw new ImplementationNotFoundError(id);
    }
    return item;
  }

  public getAll(): ImplementationBase[] {
    return Array.from(this.items.values());
  }

  public remove(id: string): void {
    this.items.delete(id);
  }
}
