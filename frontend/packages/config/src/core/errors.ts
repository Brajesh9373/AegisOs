import { PlatformError } from '@aegisos/shared';

export class ConfigurationError extends PlatformError {
  constructor(message: string, metadata?: Record<string, unknown>) {
    super(message, 'CONFIGURATION_ERROR', false, metadata);
  }
}
