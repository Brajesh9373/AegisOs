/**
 * Groups an array of objects by a specific key.
 */
export function groupBy(array, key) {
    return array.reduce((acc, item) => {
        const groupKey = String(item[key]);
        if (!acc[groupKey])
            acc[groupKey] = [];
        acc[groupKey].push(item);
        return acc;
    }, {});
}
/**
 * Splits an array into chunks of a specified size.
 */
export function chunk(array, size) {
    if (size <= 0)
        return [array];
    const result = [];
    for (let i = 0; i < array.length; i += size) {
        result.push(array.slice(i, i + size));
    }
    return result;
}
/**
 * Removes duplicate items from an array based on a selector function.
 */
export function uniqueBy(array, selector) {
    const seen = new Set();
    return array.filter((item) => {
        const val = selector(item);
        if (seen.has(val))
            return false;
        seen.add(val);
        return true;
    });
}
