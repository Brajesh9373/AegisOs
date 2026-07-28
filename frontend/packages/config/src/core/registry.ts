import { RootConfig } from '../schemas';
import { ConfigurationError } from './errors';

/**
 * Singleton registry holding the immutable configuration object.
 */
export class ConfigurationRegistry {
  private static instance: RootConfig | null = null;

  static set(config: RootConfig): void {
    if (this.instance) {
      throw new ConfigurationError('Configuration has already been initialized and is immutable.');
    }
    this.instance = Object.freeze(config);
  }

  static get(): RootConfig {
    if (!this.instance) {
      throw new ConfigurationError(
        'Configuration has not been initialized. Call ConfigurationRegistry.set() first.',
      );
    }
    return this.instance;
  }

  /**
   * Strictly for testing purposes. Do not use in production runtime.
   */
  static _reset(): void {
    this.instance = null;
  }
}
