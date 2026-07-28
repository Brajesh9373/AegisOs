import { ProviderBase } from './registry.js';
import { PlatformError } from '@aegisos/shared';

export class ProviderValidationError extends PlatformError {
  constructor(message: string) {
    super(`Provider Validation Error: ${message}`);
  }
}

export class ProviderValidation {
  public validate(item: ProviderBase): void {
    if (!item.id || !item.name) {
      throw new ProviderValidationError('Missing required fields');
    }
  }
}
