/**
 * Groups an array of objects by a specific key.
 */
export function groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {
  return array.reduce(
    (acc, item) => {
      const groupKey = String(item[key]);
      if (!acc[groupKey]) acc[groupKey] = [];
      acc[groupKey].push(item);
      return acc;
    },
    {} as Record<string, T[]>,
  );
}

/**
 * Splits an array into chunks of a specified size.
 */
export function chunk<T>(array: T[], size: number): T[][] {
  if (size <= 0) return [array];
  const result: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    result.push(array.slice(i, i + size));
  }
  return result;
}

/**
 * Removes duplicate items from an array based on a selector function.
 */
export function uniqueBy<T, K>(array: T[], selector: (item: T) => K): T[] {
  const seen = new Set<K>();
  return array.filter((item) => {
    const val = selector(item);
    if (seen.has(val)) return false;
    seen.add(val);
    return true;
  });
}
