import { PlatformError, ILogger } from '@aegisos/shared';

export class ErrorBoundary {
  constructor(private readonly logger: ILogger) {}

  public trap(error: unknown): PlatformError {
    if (error instanceof PlatformError) {
      this.logger.error(`[PlatformError] ${error.code}: ${error.message}`, error.metadata);
      return error;
    }

    const err = error instanceof Error ? error : new Error(String(error));
    this.logger.error(`[UnhandledException] ${err.message}`, { stack: err.stack });

    return new PlatformError('An unexpected runtime error occurred', 'UNHANDLED_EXCEPTION', false, {
      originalMessage: err.message,
    });
  }

  public registerProcessHooks(): void {
    if (typeof process !== 'undefined') {
      process.on('uncaughtException', (err) => this.trap(err));
      process.on('unhandledRejection', (reason) => this.trap(reason));
    }
  }
}
