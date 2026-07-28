
import { StorageProvider } from '../core/StorageProvider.js';
import crypto from 'crypto';
const uuidv4 = () => crypto.randomUUID();

export class UserRepository {
  constructor(private storage: StorageProvider) {}
  
  async create(user: Record<string, unknown>): Promise<void> {
    const id = uuidv4();
    await this.storage.execute(
      'INSERT INTO users (id, email, passwordHash, role, department, active) VALUES (?, ?, ?, ?, ?, ?)',
      [id, user.email, user.passwordHash, user.role, user.department, 1]
    );
  }

  async clear(): Promise<void> {
    await this.storage.execute('DELETE FROM users');
  }
  
  async getByEmail(email: string): Promise<Record<string, unknown>> {
    const rows = await this.storage.query<Record<string, unknown>>('SELECT * FROM users WHERE email = ?', [email]);
    return rows[0];
  }

  async getById(id: string): Promise<Record<string, unknown>> {
    const rows = await this.storage.query<Record<string, unknown>>('SELECT * FROM users WHERE id = ?', [id]);
    return rows[0];
  }

  async getAll(): Promise<Record<string, unknown>[]> {
    return this.storage.query<Record<string, unknown>>('SELECT * FROM users');
  }

  async update(id: string, updates: Record<string, unknown>): Promise<void> {
    const fields = Object.keys(updates).map(k => `${k} = ?`).join(', ');
    const values = Object.values(updates);
    values.push(id);
    await this.storage.execute(`UPDATE users SET ${fields} WHERE id = ?`, values);
  }
}
