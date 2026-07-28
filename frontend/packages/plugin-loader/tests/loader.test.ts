import { describe, it, expect } from 'vitest';
import { PluginRegistry, PluginLoader, PluginType, PluginLifecycleState } from '../src/index.js';

describe('Plugin Loader', () => {
  it('should load and unload a plugin', async () => {
    const registry = new PluginRegistry();
    const loader = new PluginLoader(registry);

    await loader.load({
      id: 'test-plugin',
      name: 'Test',
      version: '1.0.0',
      type: PluginType.Provider,
      dependencies: {},
      capabilities: [],
    });

    const plugin = registry.get('test-plugin');
    expect(plugin).toBeDefined();
    expect(plugin?.state).toBe(PluginLifecycleState.Ready);
    expect(plugin?.health).toBe('healthy');

    await loader.unload('test-plugin');
    expect(registry.get('test-plugin')).toBeUndefined();
  });
});
