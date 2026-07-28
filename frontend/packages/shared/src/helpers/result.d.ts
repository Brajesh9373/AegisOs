import { Result, Success, Failure } from '@aegisos/types';
/**
 * Type guard for Success result.
 */
export declare function isSuccess<T, E>(result: Result<T, E>): result is Success<T>;
/**
 * Type guard for Failure result.
 */
export declare function isFailure<T, E>(result: Result<T, E>): result is Failure<E>;
/**
 * Safely unwraps a Result. Returns the value if successful, or throws the Error if failed.
 * Use with caution, as it bypasses the safety of the Monad pattern.
 */
export declare function unwrap<T>(result: Result<T, Error>): T;
