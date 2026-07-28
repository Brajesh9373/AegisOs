import { describe, it, expect } from 'vitest';
import { SecurityEngine, DataProtection } from '../src/index';

describe('SecurityEngine', () => {
  it('should initialize and authenticate', () => {
    const engine = new SecurityEngine();
    const identity = engine.authenticate('token-123');
    expect(identity.userId).toBe('user-1');
  });

  it('should redact PII', () => {
    const data = new DataProtection();
    const redacted = data.redactPII('SSN is 123456789');
    expect(redacted).toBe('SSN is XXX-XX-XXXX');
  });
});
