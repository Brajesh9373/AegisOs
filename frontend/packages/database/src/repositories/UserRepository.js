import crypto from 'crypto';
const uuidv4 = () => crypto.randomUUID();
export class UserRepository {
    storage;
    constructor(storage) {
        this.storage = storage;
    }
    async create(user) {
        const id = uuidv4();
        await this.storage.execute('INSERT INTO users (id, email, passwordHash, role, department, active) VALUES (?, ?, ?, ?, ?, ?)', [id, user.email, user.passwordHash, user.role, user.department, 1]);
    }
    async clear() {
        await this.storage.execute('DELETE FROM users');
    }
    async getByEmail(email) {
        const rows = await this.storage.query('SELECT * FROM users WHERE email = ?', [email]);
        return rows[0];
    }
    async getById(id) {
        const rows = await this.storage.query('SELECT * FROM users WHERE id = ?', [id]);
        return rows[0];
    }
    async getAll() {
        return this.storage.query('SELECT * FROM users');
    }
    async update(id, updates) {
        const fields = Object.keys(updates).map(k => `${k} = ?`).join(', ');
        const values = Object.values(updates);
        values.push(id);
        await this.storage.execute(`UPDATE users SET ${fields} WHERE id = ?`, values);
    }
}
