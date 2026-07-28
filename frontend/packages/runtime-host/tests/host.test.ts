import { describe, it, expect } from 'vitest';
import { RuntimeBootstrap, HostState } from '../src/index.js';

describe('Runtime Host', () => {
  it('should transition through startup pipeline successfully', async () => {
    const host = new RuntimeBootstrap();
    expect(host.lifecycle.state).toBe(HostState.Startup);

    await host.start({ environment: 'test' });

    expect(host.lifecycle.state).toBe(HostState.Running);
    expect(host.getContext().executionId).toBeDefined();

    const health = host.diagnostics.checkHealth();
    expect(health.status).toBe('healthy');

    await host.shutdown();
    expect(host.lifecycle.state).toBe(HostState.Stopped);
  });
});
