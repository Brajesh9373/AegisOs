import { describe, it, expect } from 'vitest';
import { MemoryRegistry } from '../src/core/registry.js';
import { MemoryPolicies } from '../src/core/policies.js';
import { MemoryRetentionRules } from '../src/core/retention.js';
import { MemoryType } from '../src/core/types.js';

describe('Memory Engine', () => {
  it('should initialize registry', () => {
    const registry = new MemoryRegistry();
    expect(registry).toBeDefined();
  });

  it('should have policies', () => {
    const policies = new MemoryPolicies();
    expect(policies.canStore(MemoryType.Working)).toBe(true);
  });

  it('should have retention rules', () => {
    const retention = new MemoryRetentionRules();
    expect(retention.getRetentionPeriod(MemoryType.Working)).toBeGreaterThan(0);
  });
});
