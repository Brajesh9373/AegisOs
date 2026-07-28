import { RootConfigSchema, RootConfig } from '../schemas';
import { ConfigurationError } from './errors';
import { Result, ok, fail } from '@aegisos/types';

/**
 * Factory for creating partial configuration overwrites or specific instances programmatically.
 */
export class ConfigurationFactory {
  /**
   * Creates a verified RootConfig by deeply merging defaults with provided overrides.
   */
  static create(overrides: Record<string, unknown>): Result<RootConfig, ConfigurationError> {
    const parsed = RootConfigSchema.safeParse(overrides);
    if (!parsed.success) {
      return fail(
        new ConfigurationError('Factory validation failed', { issues: parsed.error.issues }),
      );
    }
    return ok(parsed.data as RootConfig);
  }
}
