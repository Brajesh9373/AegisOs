/**
 * Converts SQLite-style '?' placeholders to PostgreSQL-style '$1, $2, ...' placeholders.
 * Handles quoted strings to avoid replacing ? inside string literals.
 */
export function convertPlaceholders(sql: string): string {
  let index = 0;
  let result = '';
  let inSingleQuote = false;
  let inDoubleQuote = false;

  for (let i = 0; i < sql.length; i++) {
    const ch = sql[i];

    if (ch === "'" && !inDoubleQuote) {
      // Handle escaped single quotes ('')
      if (inSingleQuote && i + 1 < sql.length && sql[i + 1] === "'") {
        result += "''";
        i++;
        continue;
      }
      inSingleQuote = !inSingleQuote;
      result += ch;
    } else if (ch === '"' && !inSingleQuote) {
      inDoubleQuote = !inDoubleQuote;
      result += ch;
    } else if (ch === '?' && !inSingleQuote && !inDoubleQuote) {
      index++;
      result += `$${index}`;
    } else {
      result += ch;
    }
  }

  return result;
}
