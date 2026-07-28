import { describe, it, expect } from 'vitest';
import { ConnectorCenterService } from '../src/index';
import { SecurityEngine } from '@aegisos/security';

describe('ConnectorCenterService', () => {
  it('initializes', () => {
    const security = new SecurityEngine();
    const service = new ConnectorCenterService(security);
    expect(service).toBeDefined();
  });
});
