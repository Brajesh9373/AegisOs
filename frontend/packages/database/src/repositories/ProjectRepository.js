import crypto from 'crypto';
const uuidv4 = () => crypto.randomUUID();
export class ProjectRepository {
    storage;
    constructor(storage) {
        this.storage = storage;
    }
    async create(project, userId) {
        const id = uuidv4();
        const now = new Date().toISOString();
        await this.storage.execute('INSERT INTO projects (id, name, description, businessGoal, ownerId, department, status, priority, tags, createdAt, updatedAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [
            id,
            project.name || null,
            project.description || null,
            project.businessGoal || null,
            project.ownerId || userId,
            project.department || null,
            project.status || 'Planning',
            project.priority || 'Medium',
            JSON.stringify(project.tags || []),
            now,
            now
        ]);
        await this.storage.execute('INSERT INTO audit_logs (id, action, userId, details) VALUES (?, ?, ?, ?)', [uuidv4(), 'Project Created', userId, `Created project: ${project.name} (${id})`]);
        return this.getById(id);
    }
    async getById(id) {
        const rows = await this.storage.query('SELECT * FROM projects WHERE id = ?', [id]);
        if (rows[0] && rows[0].tags) {
            try {
                rows[0].tags = JSON.parse(rows[0].tags);
            }
            catch {
                rows[0].tags = [];
            }
        }
        return rows[0];
    }
    async getAll() {
        const rows = await this.storage.query('SELECT * FROM projects ORDER BY createdAt DESC');
        return rows.map(r => {
            if (r.tags) {
                try {
                    r.tags = JSON.parse(r.tags);
                }
                catch {
                    r.tags = [];
                }
            }
            return r;
        });
    }
    async update(id, updates, userId) {
        updates.updatedAt = new Date().toISOString();
        if (updates.tags)
            updates.tags = JSON.stringify(updates.tags);
        const fields = Object.keys(updates).map(k => `${k} = ?`).join(', ');
        const values = Object.values(updates);
        values.push(id);
        await this.storage.execute(`UPDATE projects SET ${fields} WHERE id = ?`, values);
        await this.storage.execute('INSERT INTO audit_logs (id, action, userId, details) VALUES (?, ?, ?, ?)', [uuidv4(), 'Project Updated', userId, `Updated project: ${id}`]);
    }
    async delete(id, userId) {
        await this.storage.execute('DELETE FROM projects WHERE id = ?', [id]);
        await this.storage.execute('INSERT INTO audit_logs (id, action, userId, details) VALUES (?, ?, ?, ?)', [uuidv4(), 'Project Deleted', userId, `Deleted project: ${id}`]);
    }
}
