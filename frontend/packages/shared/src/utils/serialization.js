import { ok, fail } from '@aegisos/types';
/**
 * Safely parses a JSON string, returning a monadic Result instead of throwing.
 */
export function safeJsonParse(json) {
    try {
        return ok(JSON.parse(json));
    }
    catch (err) {
        return fail(err instanceof Error ? err : new Error('Invalid JSON format'));
    }
}
/**
 * Safely stringifies an object, handling circular references via fallback.
 */
export function safeJsonStringify(obj) {
    try {
        return ok(JSON.stringify(obj));
    }
    catch (err) {
        return fail(err instanceof Error ? err : new Error('JSON stringify failed'));
    }
}
