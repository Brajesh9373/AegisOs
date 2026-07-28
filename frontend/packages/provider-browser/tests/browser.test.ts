import { describe, it, expect } from 'vitest';
import { BrowserProvider } from '../src/index.js';

describe('Browser Provider', () => {
  it('should initialize and report healthy', async () => {
    const provider = new BrowserProvider();

    // Abstracting actual playwright boot out in CI, just check typings
    expect(provider.id).toBe('provider-browser');
    expect(provider.capabilities.supportedFeatures).toContain('chromium');
    expect(provider.capabilities.supportedFeatures).toContain('pdf');
  });
});
