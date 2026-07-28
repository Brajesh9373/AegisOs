import { PlatformError } from '@aegisos/shared';

export class RegistryError extends PlatformError {
  constructor(message: string) {
    super(message, 'REGISTRY_ERROR', false);
  }
}

export class BaseRegistry<T> {
  protected readonly items = new Map<string, T>();

  public register(id: string, item: T): void {
    if (this.items.has(id)) {
      throw new RegistryError(`Item with ID ${id} already registered`);
    }
    this.items.set(id, item);
  }

  public get(id: string): T {
    const item = this.items.get(id);
    if (!item) {
      throw new RegistryError(`Item with ID ${id} not found`);
    }
    return item;
  }

  public getAll(): T[] {
    return Array.from(this.items.values());
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export class ServiceRegistry extends BaseRegistry<any> {}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export class CapabilityRegistry extends BaseRegistry<any> {}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export class ModuleRegistry extends BaseRegistry<any> {}
