import { Result, ok, fail } from '@aegisos/types';

/**
 * Safely parses a JSON string, returning a monadic Result instead of throwing.
 */
export function safeJsonParse<T = unknown>(json: string): Result<T> {
  try {
    return ok(JSON.parse(json) as T);
  } catch (err) {
    return fail(err instanceof Error ? err : new Error('Invalid JSON format'));
  }
}

/**
 * Safely stringifies an object, handling circular references via fallback.
 */
export function safeJsonStringify(obj: unknown): Result<string> {
  try {
    return ok(JSON.stringify(obj));
  } catch (err) {
    return fail(err instanceof Error ? err : new Error('JSON stringify failed'));
  }
}
