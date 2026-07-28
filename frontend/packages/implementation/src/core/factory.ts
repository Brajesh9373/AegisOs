import { ImplementationBase } from './registry.js';

export class ImplementationFactory {
  public createImplementation(id: string, name: string): ImplementationBase {
    return {
      id,
      name,
      version: '1.0.0',
      description: 'Auto-generated implementation',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  }
}
