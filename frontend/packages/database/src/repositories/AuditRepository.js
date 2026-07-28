import crypto from 'crypto';
const uuidv4 = () => crypto.randomUUID();
export class AuditRepository {
    storage;
    constructor(storage) {
        this.storage = storage;
    }
    async log(action, userId, details) {
        const id = uuidv4();
        await this.storage.execute('INSERT INTO audit_logs (id, action, userId, details) VALUES (?, ?, ?, ?)', [id, action, userId, details]);
    }
}
