import { Result, Success, Failure } from '@aegisos/types';

/**
 * Type guard for Success result.
 */
export function isSuccess<T, E>(result: Result<T, E>): result is Success<T> {
  return result.success === true;
}

/**
 * Type guard for Failure result.
 */
export function isFailure<T, E>(result: Result<T, E>): result is Failure<E> {
  return result.success === false;
}

/**
 * Safely unwraps a Result. Returns the value if successful, or throws the Error if failed.
 * Use with caution, as it bypasses the safety of the Monad pattern.
 */
export function unwrap<T>(result: Result<T, Error>): T {
  if (isFailure(result)) {
    throw result.error;
  }
  return result.value;
}
