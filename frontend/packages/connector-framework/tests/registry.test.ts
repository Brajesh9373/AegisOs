import { describe, it, expect } from 'vitest';
import { ConnectorRegistry } from '../src/core/registry';
describe('ConnectorRegistry', () => {
  it('registers', () => {
    const reg = new ConnectorRegistry();
    expect(reg).toBeDefined();
  });
});
