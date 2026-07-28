/**
 * Monadic Result types representing deterministic execution outcomes.
 * Completely eliminates the need for try/catch exception throwing in business logic.
 */

export type Success<T> = {
  success: true;
  value: T;
};

export type Failure<E = Error> = {
  success: false;
  error: E;
};

/**
 * The standard return type for all aegisOS operations.
 * Must be checked via `.success` before accessing `.value` or `.error`.
 */
export type Result<T, E = Error> = Success<T> | Failure<E>;

/**
 * Helper to construct a Success result.
 */
export const ok = <T>(value: T): Success<T> => ({ success: true, value });

/**
 * Helper to construct a Failure result.
 */
export const fail = <E>(error: E): Failure<E> => ({ success: false, error });
