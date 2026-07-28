import { describe, it, expect } from 'vitest';
import { ImplementationRegistry, ImplementationFactory } from '../src/index.js';

describe('Implementation Engine', () => {
  it('should initialize registry', () => {
    const registry = new ImplementationRegistry();
    expect(registry).toBeDefined();
  });

  it('should create implementation', () => {
    const factory = new ImplementationFactory();
    const impl = factory.createImplementation('impl-1', 'Test Impl');
    expect(impl.id).toBe('impl-1');
  });
});
