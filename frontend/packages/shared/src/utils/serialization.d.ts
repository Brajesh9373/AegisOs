import { Result } from '@aegisos/types';
/**
 * Safely parses a JSON string, returning a monadic Result instead of throwing.
 */
export declare function safeJsonParse<T = unknown>(json: string): Result<T>;
/**
 * Safely stringifies an object, handling circular references via fallback.
 */
export declare function safeJsonStringify(obj: unknown): Result<string>;
