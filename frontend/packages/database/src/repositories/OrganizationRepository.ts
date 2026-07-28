import { StorageProvider } from '../core/StorageProvider.js';

export class OrganizationRepository {
  constructor(private storage: StorageProvider) {}

  async get(): Promise<Record<string, unknown> | null> {
    const rows = await this.storage.query<Record<string, unknown>>('SELECT * FROM organization');
    return rows.length > 0 ? rows[0] : null;
  }

  async clear(): Promise<void> {
    await this.storage.execute('DELETE FROM organization');
  }

  async create(org: { id: string; name: string; domain: string; licenseKey: string; aiProvider: string; aiApiKey: string; aiModel: string; storage: string; database: string }): Promise<void> {
    await this.storage.execute(
      'INSERT INTO organization (id, name, domain, setupComplete, licenseKey, aiProvider, aiApiKey, aiModel, storage, database) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
      [org.id, org.name, org.domain, 1, org.licenseKey, org.aiProvider, org.aiApiKey, org.aiModel, org.storage, org.database]
    );
  }
}
