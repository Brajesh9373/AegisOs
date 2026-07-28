import { BaseEntity } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';

// For foundation purposes we'll define a KnowledgeBase representation
export interface KnowledgeBase extends BaseEntity {
  name: string;
  version: string;
  description: string;
  sourceType: string;
}

export class KnowledgeNotFoundError extends PlatformError {
  constructor(id: string) {
    super(`Knowledge with ID ${id} not found`);
  }
}

export class KnowledgeRegistry {
  private items = new Map<string, KnowledgeBase>();

  public register(item: KnowledgeBase): void {
    this.items.set(item.id, item);
  }

  public get(id: string): KnowledgeBase {
    const item = this.items.get(id);
    if (!item) {
      throw new KnowledgeNotFoundError(id);
    }
    return item;
  }

  public getAll(): KnowledgeBase[] {
    return Array.from(this.items.values());
  }

  public remove(id: string): void {
    this.items.delete(id);
  }
}
