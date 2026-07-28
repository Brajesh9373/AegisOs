export class SessionRepository {
    storage;
    constructor(storage) {
        this.storage = storage;
    }
    async create(id, userId, token, expiresAt) {
        await this.storage.execute('INSERT INTO sessions (id, userId, token, expiresAt) VALUES (?, ?, ?, ?)', [id, userId, token, expiresAt]);
    }
    async getByToken(token) {
        const rows = await this.storage.query('SELECT * FROM sessions WHERE token = ?', [token]);
        return rows.length > 0 ? rows[0] : null;
    }
    async deleteByToken(token) {
        await this.storage.execute('DELETE FROM sessions WHERE token = ?', [token]);
    }
}
