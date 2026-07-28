import { describe, it, expect } from 'vitest';
import {
  SkillFactory,
  SkillRegistry,
  SkillLifecycle,
  SkillDependencyGraph,
  SkillPermissionRegistry,
} from '../src/index.js';

describe('Skill Engine Foundation', () => {
  it('Factory creates valid skills', () => {
    const skill = SkillFactory.create('data-extractor', '1.0.0', 'Extracts data');
    expect(skill.id).toBeDefined();
    expect(skill.name).toBe('data-extractor');
    expect(skill.version).toBe('1.0.0');
  });

  it('Registry manages skills', () => {
    const registry = new SkillRegistry();
    const skill = SkillFactory.create('data-extractor', '1.0.0', 'Extracts data');

    registry.register(skill);
    expect(registry.get(skill.id)).toEqual(skill);
    expect(registry.getAll().length).toBe(1);

    registry.remove(skill.id);
    expect(() => registry.get(skill.id)).toThrowError(/not found/);
  });

  it('Lifecycle enforces valid transitions', () => {
    const lifecycle = new SkillLifecycle();
    expect(lifecycle.getState()).toBe('Unregistered');

    lifecycle.transition('Registered');
    expect(lifecycle.getState()).toBe('Registered');

    expect(() => lifecycle.transition('Unregistered')).not.toThrow();
  });

  it('Dependency Graph resolves order', () => {
    const graph = new SkillDependencyGraph();
    graph.addDependency('B', 'A');
    graph.addDependency('C', 'B');

    const order = graph.resolveOrder(['C']);
    expect(order).toEqual(['A', 'B', 'C']);
  });

  it('Permission Registry handles permissions', () => {
    const perms = new SkillPermissionRegistry();
    perms.grantPermission('skill-1', 'network.read');

    expect(perms.hasPermission('skill-1', 'network.read')).toBe(true);
    expect(perms.hasPermission('skill-1', 'file.read')).toBe(false);
  });
});
