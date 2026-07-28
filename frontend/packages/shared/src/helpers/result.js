/**
 * Type guard for Success result.
 */
export function isSuccess(result) {
    return result.success === true;
}
/**
 * Type guard for Failure result.
 */
export function isFailure(result) {
    return result.success === false;
}
/**
 * Safely unwraps a Result. Returns the value if successful, or throws the Error if failed.
 * Use with caution, as it bypasses the safety of the Monad pattern.
 */
export function unwrap(result) {
    if (isFailure(result)) {
        throw result.error;
    }
    return result.value;
}
