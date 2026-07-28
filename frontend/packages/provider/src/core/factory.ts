import { ProviderBase } from './registry.js';

export class ProviderFactory {
  public createProvider(id: string, name: string): ProviderBase {
    return {
      id,
      name,
      version: '1.0.0',
      description: 'Auto-generated provider',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  }
}
