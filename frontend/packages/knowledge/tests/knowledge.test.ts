import { describe, it, expect } from 'vitest';
import {
  KnowledgeFactory,
  KnowledgeRegistry,
  KnowledgeLifecycle,
  KnowledgeDependencyGraph,
  KnowledgePermissionRegistry,
} from '../src/index.js';

describe('Knowledge Engine Foundation', () => {
  it('Factory creates valid knowledge items', () => {
    const item = KnowledgeFactory.create(
      'company-docs',
      '1.0.0',
      'Company Documentation',
      'markdown',
    );
    expect(item.id).toBeDefined();
    expect(item.name).toBe('company-docs');
    expect(item.version).toBe('1.0.0');
    expect(item.sourceType).toBe('markdown');
  });

  it('Registry manages knowledge items', () => {
    const registry = new KnowledgeRegistry();
    const item = KnowledgeFactory.create(
      'company-docs',
      '1.0.0',
      'Company Documentation',
      'markdown',
    );

    registry.register(item);
    expect(registry.get(item.id)).toEqual(item);
    expect(registry.getAll().length).toBe(1);

    registry.remove(item.id);
    expect(() => registry.get(item.id)).toThrowError(/not found/);
  });

  it('Lifecycle enforces valid transitions', () => {
    const lifecycle = new KnowledgeLifecycle();
    expect(lifecycle.getState()).toBe('Draft');

    lifecycle.transition('Published');
    expect(lifecycle.getState()).toBe('Published');

    expect(() => lifecycle.transition('Draft')).not.toThrow();
  });

  it('Dependency Graph manages edges', () => {
    const graph = new KnowledgeDependencyGraph();
    graph.addDependency('B', 'A');

    expect(graph.getDependencies('B')).toEqual(['A']);
  });

  it('Permission Registry handles permissions', () => {
    const perms = new KnowledgePermissionRegistry();
    perms.grantPermission('knowledge-1', 'read');

    expect(perms.hasPermission('knowledge-1', 'read')).toBe(true);
    expect(perms.hasPermission('knowledge-1', 'write')).toBe(false);
  });
});
