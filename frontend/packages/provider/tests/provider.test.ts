import { describe, it, expect } from 'vitest';
import { ProviderRegistry, ProviderFactory } from '../src/index.js';

describe('Provider Framework', () => {
  it('should initialize registry', () => {
    const registry = new ProviderRegistry();
    expect(registry).toBeDefined();
  });

  it('should create providers', () => {
    const factory = new ProviderFactory();
    const provider = factory.createProvider('provider-1', 'Test Provider');
    expect(provider.id).toBe('provider-1');
  });
});
