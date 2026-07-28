/**
 * Returns the current date and time in strict ISO 8601 format.
 */
export function currentIsoTimestamp(): string {
  return new Date().toISOString();
}

/**
 * Calculates the difference between two timestamps in milliseconds.
 */
export function durationMs(startIso: string, endIso: string): number {
  return new Date(endIso).getTime() - new Date(startIso).getTime();
}

/**
 * Halts execution for the specified number of milliseconds.
 * Useful for async retry loops.
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
