/**
 * Returns the current date and time in strict ISO 8601 format.
 */
export declare function currentIsoTimestamp(): string;
/**
 * Calculates the difference between two timestamps in milliseconds.
 */
export declare function durationMs(startIso: string, endIso: string): number;
/**
 * Halts execution for the specified number of milliseconds.
 * Useful for async retry loops.
 */
export declare function sleep(ms: number): Promise<void>;
