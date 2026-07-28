import { PlatformError } from '@aegisos/shared';

export class KnowledgeValidationError extends PlatformError {
  constructor(message: string) {
    super(message);
  }
}

export class KnowledgeValidator {
  public static validate(rawItem: unknown): boolean {
    const item = rawItem as Record<string, unknown>;
    if (!item || !item.id || !item.name || !item.version) {
      throw new KnowledgeValidationError('Invalid knowledge base structure');
    }
    return true;
  }
}
