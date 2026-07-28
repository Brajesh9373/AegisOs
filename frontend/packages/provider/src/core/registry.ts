import { BaseEntity } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';

export interface ProviderBase extends BaseEntity {
  name: string;
  version: string;
  description: string;
}

export class ProviderNotFoundError extends PlatformError {
  constructor(id: string) {
    super(`Provider with ID ${id} not found`);
  }
}

export class ProviderRegistry {
  private items = new Map<string, ProviderBase>();

  public register(item: ProviderBase): void {
    this.items.set(item.id, item);
  }

  public get(id: string): ProviderBase {
    const item = this.items.get(id);
    if (!item) {
      throw new ProviderNotFoundError(id);
    }
    return item;
  }

  public getAll(): ProviderBase[] {
    return Array.from(this.items.values());
  }

  public remove(id: string): void {
    this.items.delete(id);
  }
}
