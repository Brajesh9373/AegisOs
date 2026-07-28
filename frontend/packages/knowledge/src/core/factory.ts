import { generateId } from '@aegisos/shared';
import { KnowledgeBase } from './registry.js';

export class KnowledgeFactory {
  public static create(
    name: string,
    version: string,
    description: string,
    sourceType: string,
  ): KnowledgeBase {
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
