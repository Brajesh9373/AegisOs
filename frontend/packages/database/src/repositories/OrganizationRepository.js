export class OrganizationRepository {
    storage;
    constructor(storage) {
        this.storage = storage;
    }
    async get() {
        const rows = await this.storage.query('SELECT * FROM organization');
        return rows.length > 0 ? rows[0] : null;
    }
    async clear() {
        await this.storage.execute('DELETE FROM organization');
    }
    async create(org) {
        await this.storage.execute('INSERT INTO organization (id, name, domain, setupComplete, licenseKey, aiProvider, aiApiKey, aiModel, storage, database) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [org.id, org.name, org.domain, 1, org.licenseKey, org.aiProvider, org.aiApiKey, org.aiModel, org.storage, org.database]);
    }
}
