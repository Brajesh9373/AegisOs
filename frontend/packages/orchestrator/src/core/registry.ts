import { BaseEntity } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';

export interface OrchestratorBase extends BaseEntity {
  name: string;
  version: string;
  description: string;
}

export class OrchestratorNotFoundError extends PlatformError {
  constructor(id: string) {
    super(`Orchestrator with ID ${id} not found`);
  }
}

export class OrchestratorRegistry {
  private items = new Map<string, OrchestratorBase>();

  public register(item: OrchestratorBase): void {
    this.items.set(item.id, item);
  }

  public get(id: string): OrchestratorBase {
    const item = this.items.get(id);
    if (!item) {
      throw new OrchestratorNotFoundError(id);
    }
    return item;
  }

  public getAll(): OrchestratorBase[] {
    return Array.from(this.items.values());
  }

  public remove(id: string): void {
    this.items.delete(id);
  }
}
