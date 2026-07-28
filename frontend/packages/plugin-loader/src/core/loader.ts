import { PluginRegistry } from './registry.js';
import { PluginValidation } from './validation.js';
import { PluginManifest, PluginLifecycleState } from './types.js';

export class PluginLoader {
  private validation = new PluginValidation();

  constructor(private registry: PluginRegistry) {}

  public async load(manifest: PluginManifest): Promise<void> {
    this.validation.validateManifest(manifest);
    const instance = this.registry.register(manifest);

    // Lifecycle transition
    instance.state = PluginLifecycleState.Load;
    instance.state = PluginLifecycleState.Initialize;
    instance.state = PluginLifecycleState.Ready;
    instance.health = 'healthy';
  }

  public async unload(id: string): Promise<void> {
    const instance = this.registry.get(id);
    if (!instance) throw new Error('Plugin not found');

    instance.state = PluginLifecycleState.Disable;
    instance.state = PluginLifecycleState.Unload;
    instance.state = PluginLifecycleState.Remove;
    this.registry.remove(id);
  }
}
