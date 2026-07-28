/**
 * Groups an array of objects by a specific key.
 */
export declare function groupBy<T>(array: T[], key: keyof T): Record<string, T[]>;
/**
 * Splits an array into chunks of a specified size.
 */
export declare function chunk<T>(array: T[], size: number): T[][];
/**
 * Removes duplicate items from an array based on a selector function.
 */
export declare function uniqueBy<T, K>(array: T[], selector: (item: T) => K): T[];
