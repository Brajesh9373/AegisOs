import { UniversalConnector } from '@aegisos/contracts';
export class LegacyProviderAdapter {
  constructor(private legacyProvider: unknown) {}
  toConnector(): UniversalConnector {
    return {
      id: 'legacy-adapter-' + Date.now(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      name: 'LegacyAdapter',
      version: '1.0',
      state: 'REGISTERED',
      supportedModalities: ['Batch'],
    };
  }
}
