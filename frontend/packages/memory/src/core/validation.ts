import { PlatformError } from '@aegisos/shared';

export class MemoryValidationError extends PlatformError {
  constructor(message: string) {
    super(message);
  }
}

export class MemoryValidator {
  public static validate(rawItem: unknown): boolean {
    const item = rawItem as Record<string, unknown>;
    if (!item || !item.id || !item.name || !item.version) {
      throw new MemoryValidationError('Invalid memory base structure');
    }
    return true;
  }
}
