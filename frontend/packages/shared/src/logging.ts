/**
 * The standard Logging contract.
 * We do not implement the concrete logger here (e.g., Winston/Pino),
 * we only expose the strict interface expected by dependency injection.
 */
export interface ILogger {
  info(message: string, meta?: Record<string, unknown>): void;
  warn(message: string, meta?: Record<string, unknown>): void;
  error(message: string, meta?: Record<string, unknown>): void;
  debug(message: string, meta?: Record<string, unknown>): void;
}
