import { PluginManifest } from './types.js';

export class PluginValidation {
  public validateManifest(manifest: PluginManifest): void {
    if (!manifest.id || !manifest.name || !manifest.version || !manifest.type) {
      throw new Error('Invalid Plugin Manifest: Missing required fields');
    }
  }

  public validateCompatibility(pluginVersion: string, runtimeVersion: string): boolean {
    // Abstract version validation
    return pluginVersion !== '' && runtimeVersion !== '';
  }

  public validateDependencies(manifest: PluginManifest, availablePlugins: string[]): void {
    const missing = Object.keys(manifest.dependencies).filter(
      (dep) => !availablePlugins.includes(dep),
    );
    if (missing.length > 0) {
      throw new Error(`Missing dependencies: ${missing.join(', ')}`);
    }
  }
}
