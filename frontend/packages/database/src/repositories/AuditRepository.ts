import { StorageProvider } from '../core/StorageProvider.js';
import crypto from 'crypto';
const uuidv4 = () => crypto.randomUUID();

export class AuditRepository {
  constructor(private storage: StorageProvider) {}

  async log(action: string, userId: string, details: string): Promise<void> {
    const id = uuidv4();
    await this.storage.execute(
      'INSERT INTO audit_logs (id, action, userId, details) VALUES (?, ?, ?, ?)',
      [id, action, userId, details]
    );
  }
}
