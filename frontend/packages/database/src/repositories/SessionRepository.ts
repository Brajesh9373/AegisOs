import { StorageProvider } from '../core/StorageProvider.js';

export class SessionRepository {
  constructor(private storage: StorageProvider) {}

  async create(id: string, userId: string, token: string, expiresAt: string): Promise<void> {
    await this.storage.execute(
      'INSERT INTO auth_sessions (id, userId, token, expiresAt) VALUES (?, ?, ?, ?)',
      [id, userId, token, expiresAt]
    );
  }

  async getByToken(token: string): Promise<Record<string, unknown> | null> {
    const rows = await this.storage.query<Record<string, unknown>>('SELECT * FROM auth_sessions WHERE token = ?', [token]);
    return rows.length > 0 ? rows[0] : null;
  }

  async deleteByToken(token: string): Promise<void> {
    await this.storage.execute('DELETE FROM auth_sessions WHERE token = ?', [token]);
  }
}
