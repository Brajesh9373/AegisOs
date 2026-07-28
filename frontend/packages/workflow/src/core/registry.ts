import { BaseEntity } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';

export interface WorkflowBase extends BaseEntity {
  name: string;
  version: string;
  description: string;
}

export class WorkflowNotFoundError extends PlatformError {
  constructor(id: string) {
    super(`Workflow with ID ${id} not found`);
  }
}

export class WorkflowRegistry {
  private items = new Map<string, WorkflowBase>();

  public register(item: WorkflowBase): void {
    this.items.set(item.id, item);
  }

  public get(id: string): WorkflowBase {
    const item = this.items.get(id);
    if (!item) {
      throw new WorkflowNotFoundError(id);
    }
    return item;
  }

  public getAll(): WorkflowBase[] {
    return Array.from(this.items.values());
  }

  public remove(id: string): void {
    this.items.delete(id);
  }
}
