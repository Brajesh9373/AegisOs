import { describe, it, expect } from 'vitest';
import {
  ToolFactory,
  ToolRegistry,
  ToolLifecycle,
  ToolDependencyGraph,
  ToolPermissionRegistry,
} from '../src/index.js';

describe('Tool Engine Foundation', () => {
  it('Factory creates valid tools', () => {
    const tool = ToolFactory.create('fetch-data', '1.0.0', 'Fetches data');
    expect(tool.id).toBeDefined();
    expect(tool.name).toBe('fetch-data');
    expect(tool.version).toBe('1.0.0');
    expect(tool.isIdempotent).toBe(false);
  });

  it('Registry manages tools', () => {
    const registry = new ToolRegistry();
    const tool = ToolFactory.create('fetch-data', '1.0.0', 'Fetches data');

    registry.register(tool);
    expect(registry.get(tool.id)).toEqual(tool);
    expect(registry.getAll().length).toBe(1);

    registry.remove(tool.id);
    expect(() => registry.get(tool.id)).toThrowError(/not found/);
  });

  it('Lifecycle enforces valid transitions', () => {
    const lifecycle = new ToolLifecycle();
    expect(lifecycle.getState()).toBe('Unregistered');

    lifecycle.transition('Registered');
    expect(lifecycle.getState()).toBe('Registered');

    expect(() => lifecycle.transition('Unregistered')).not.toThrow();
  });

  it('Dependency Graph manages edges', () => {
    const graph = new ToolDependencyGraph();
    graph.addDependency('B', 'A');

    expect(graph.getDependencies('B')).toEqual(['A']);
  });

  it('Permission Registry handles permissions', () => {
    const perms = new ToolPermissionRegistry();
    perms.grantPermission('tool-1', 'network.read');

    expect(perms.hasPermission('tool-1', 'network.read')).toBe(true);
    expect(perms.hasPermission('tool-1', 'file.read')).toBe(false);
  });
});
