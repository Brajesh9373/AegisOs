import { describe, it, expect, beforeEach } from 'vitest';
import { Container, createMockRuntime } from '../src';
import { ConfigurationRegistry } from '@aegisos/config';

describe('Runtime Foundation', () => {
  beforeEach(() => {
    ConfigurationRegistry._reset();
  });

  it('Container registers and resolves values', () => {
    const container = new Container();
    container.registerValue('testToken', { value: 42 });
    const resolved = container.resolve<{ value: number }>('testToken');
    expect(resolved.value).toBe(42);
  });

  it('Container throws on duplicate registration', () => {
    const container = new Container();
    container.registerValue('token', 1);
    expect(() => container.registerValue('token', 2)).toThrowError(/already registered/);
  });

  it('Container throws on missing dependency', () => {
    const container = new Container();
    expect(() => container.resolve('missing')).toThrowError(/No provider found/);
  });

  it('RuntimeAPI bootstraps correctly', async () => {
    const api = createMockRuntime();
    expect(api.context).toBeDefined();
    expect(api.health).toBeDefined();
    expect(api.lifecycle).toBeDefined();
    expect(api.events).toBeDefined();

    const health = await api.health.checkHealth();
    expect(health.status).toBe('DOWN'); // Lifecycle not started

    await api.lifecycle.start();
    const healthUp = await api.health.checkHealth();
    expect(healthUp.status).toBe('UP');
  });
});
