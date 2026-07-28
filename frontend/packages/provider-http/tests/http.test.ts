import { describe, it, expect } from 'vitest';
import { HttpProvider, HttpRequest } from '../src/index.js';

describe('HTTP Provider', () => {
  it('should initialize correctly', async () => {
    const provider = new HttpProvider();
    await provider.initialize({ id: 'test', options: { timeout: 5000 } });

    const health = await provider.healthCheck();
    expect(health.status).toBe('healthy');
  });

  it('should trip circuit breaker after failures', async () => {
    const provider = new HttpProvider();
    await provider.initialize({
      id: 'test',
      options: { circuitBreakerThreshold: 1, maxRetries: 0, timeout: 100 },
    });

    const req: HttpRequest = { method: 'GET', url: 'http://invalid.local' };

    try {
      await provider.executeRequest(req);
    } catch {
      // Ignore initial error
    }

    await expect(provider.executeRequest(req)).rejects.toThrow('Circuit Breaker is OPEN');

    const health = await provider.healthCheck();
    expect(health.status).toBe('down');
  });
});
