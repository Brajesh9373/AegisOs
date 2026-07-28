import { ProviderBase } from '@aegisos/provider';

export interface PluginMetadata {
  id: string;
  version: string;
  entryPoint: string;
}

export class PluginRegistry {
  private plugins = new Map<string, ProviderBase>();

  public register(plugin: ProviderBase): void {
    if (this.plugins.has(plugin.id)) {
      throw new Error(`Plugin ${plugin.id} is already registered`);
    }
    this.plugins.set(plugin.id, plugin);
  }

  public get(id: string): ProviderBase | undefined {
    return this.plugins.get(id);
  }

  public getAll(): ProviderBase[] {
    return Array.from(this.plugins.values());
  }
}

export class PluginLoader {
  constructor(private registry: PluginRegistry) {}

  public async loadFromMetadata(_metadata: PluginMetadata): Promise<void> {
    // Abstract loader boundary. Actual dynamic imports would happen here.
    return Promise.resolve();
  }
}
