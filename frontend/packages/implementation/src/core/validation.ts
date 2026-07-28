import { ImplementationBase } from './registry.js';
import { PlatformError } from '@aegisos/shared';

export class ImplementationValidationError extends PlatformError {
  constructor(message: string) {
    super(`Implementation Validation Error: ${message}`);
  }
}

export class ImplementationValidation {
  public validate(item: ImplementationBase): void {
    if (!item.id || !item.name) {
      throw new ImplementationValidationError('Missing required fields');
    }
  }
}
