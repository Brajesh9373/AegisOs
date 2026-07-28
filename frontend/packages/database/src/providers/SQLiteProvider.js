import * as path from 'path';
import * as fs from 'fs';
import initSqlJs from 'sql.js';
export class SQLiteProvider {
    db = null;
    dbPath;
    constructor(filename = 'aegis.db') {
        const dataDir = path.join(process.cwd(), 'data');
        if (!fs.existsSync(dataDir)) {
            fs.mkdirSync(dataDir, { recursive: true });
        }
        this.dbPath = path.join(dataDir, filename);
    }
    async connect() {
        const SQL = await initSqlJs();
        if (fs.existsSync(this.dbPath)) {
            const buf = fs.readFileSync(this.dbPath);
            this.db = new SQL.Database(buf);
        }
        else {
            this.db = new SQL.Database();
        }
        this.initializeSchema();
        this.persist(); // save initial schema
    }
    async disconnect() {
        if (this.db) {
            this.persist();
            this.db.close();
            this.db = null;
        }
    }
    async query(sql, params = []) {
        if (!this.db)
            throw new Error('Database not connected');
        const stmt = this.db.prepare(sql);
        stmt.bind(params);
        const rows = [];
        while (stmt.step()) {
            rows.push(stmt.getAsObject());
        }
        stmt.free();
        return rows;
    }
    async execute(sql, params = []) {
        if (!this.db)
            throw new Error('Database not connected');
        this.db.run(sql, params);
        this.persist();
    }
    persist() {
        if (!this.db)
            return;
        const data = this.db.export();
        fs.writeFileSync(this.dbPath, Buffer.from(data));
    }
    initializeSchema() {
        if (!this.db)
            return;
        this.db.run(`
      CREATE TABLE IF NOT EXISTS organization (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        domain TEXT NOT NULL,
        setupComplete INTEGER NOT NULL DEFAULT 0,
        licenseKey TEXT,
        aiProvider TEXT,
        aiApiKey TEXT,
        aiModel TEXT,
        storage TEXT,
        database TEXT
      );

      CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        passwordHash TEXT NOT NULL,
        role TEXT NOT NULL,
        department TEXT,
        active INTEGER NOT NULL DEFAULT 1
      );

      CREATE TABLE IF NOT EXISTS departments (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        ownerId TEXT,
        parentId TEXT
      );

      CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        action TEXT NOT NULL,
        userId TEXT,
        details TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        userId TEXT NOT NULL,
        token TEXT NOT NULL,
        expiresAt TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        businessGoal TEXT,
        ownerId TEXT,
        department TEXT,
        status TEXT,
        priority TEXT,
        tags TEXT,
        createdAt TEXT,
        updatedAt TEXT
      );

      CREATE TABLE IF NOT EXISTS invitations (
        id TEXT PRIMARY KEY,
        orgId TEXT,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        token TEXT NOT NULL,
        expiresAt TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        projectId TEXT,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        config TEXT,
        systemPrompt TEXT
      );

      CREATE TABLE IF NOT EXISTS execution_nodes (
        id TEXT PRIMARY KEY,
        projectId TEXT,
        agentId TEXT,
        state TEXT NOT NULL,
        dependencies TEXT,
        outputs TEXT,
        reasoning TEXT
      );

      CREATE TABLE IF NOT EXISTS artifacts (
        id TEXT PRIMARY KEY,
        projectId TEXT,
        type TEXT NOT NULL,
        storagePath TEXT,
        versionHistory TEXT
      );

      CREATE TABLE IF NOT EXISTS human_queue (
        id TEXT PRIMARY KEY,
        projectId TEXT,
        agentId TEXT,
        reason TEXT NOT NULL,
        status TEXT NOT NULL,
        resolution TEXT,
        assignedTo TEXT
      );

      CREATE TABLE IF NOT EXISTS agent_memory (
        id TEXT PRIMARY KEY,
        agentId TEXT NOT NULL,
        type TEXT NOT NULL,
        key TEXT,
        value TEXT,
        embeddings TEXT
      );

      CREATE TABLE IF NOT EXISTS general_ai_sessions (
        id TEXT PRIMARY KEY,
        projectId TEXT,
        userId TEXT NOT NULL,
        stage TEXT NOT NULL,
        originalGoal TEXT NOT NULL,
        clarification TEXT,
        summary TEXT,
        createdAt TEXT NOT NULL,
        updatedAt TEXT NOT NULL
      );
    `);
    }
}
