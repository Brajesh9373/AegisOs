import { generateId } from '@aegisos/shared';
import { MemoryBase } from './registry.js';

export class MemoryFactory {
  public static create(
    name: string,
    version: string,
    description: string,
    sourceType: string,
  ): MemoryBase {
    return {
      id: generateId(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      name,
      version,
      description,
      sourceType,
    };
  }
}
