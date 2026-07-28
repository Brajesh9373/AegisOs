import { StorageProvider } from './StorageProvider.js';
import { SQLiteProvider } from '../providers/SQLiteProvider.js';
import { PostgreSQLProvider } from '../providers/PostgreSQLProvider.js';

/**
 * Creates the appropriate StorageProvider based on DATABASE_URL.
 * Falls back to SQLite if DATABASE_URL is not set.
 */
export function createProvider(): StorageProvider {
  const databaseUrl = process.env.DATABASE_URL;

  if (databaseUrl && databaseUrl.startsWith('postgresql')) {
    // Strip asyncpg driver suffix if present (Python/SQLAlchemy format)
    const pgUrl = databaseUrl.replace('postgresql+asyncpg://', 'postgresql://');
    const maskedUrl = pgUrl.replace(/:[^@]+@/, ':***@');
    console.log(`Using PostgreSQL provider: ${maskedUrl}`);
    return new PostgreSQLProvider({ connectionString: pgUrl, skipSchema: false });
  }

  console.log('Using SQLite provider (fallback)');
  return new SQLiteProvider();
}
