import { PluginInstance, PluginManifest, PluginLifecycleState } from './types.js';

export class PluginRegistry {
  private plugins = new Map<string, PluginInstance>();

  public register(manifest: PluginManifest): PluginInstance {
    if (this.plugins.has(manifest.id)) {
      throw new Error(`Plugin ${manifest.id} already registered`);
    }
    const instance: PluginInstance = {
      manifest,
      state: PluginLifecycleState.Install,
      health: 'down',
    };
    this.plugins.set(manifest.id, instance);
    return instance;
  }

  public get(id: string): PluginInstance | undefined {
    return this.plugins.get(id);
  }

  public getAll(): PluginInstance[] {
    return Array.from(this.plugins.values());
  }

  public remove(id: string): void {
    this.plugins.delete(id);
  }
}
