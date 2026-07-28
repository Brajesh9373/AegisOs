import pg from 'pg';
const { Pool } = pg;
import { StorageProvider } from '../core/StorageProvider.js';
import { convertPlaceholders } from '../core/convertPlaceholders.js';

export interface PostgreSQLProviderConfig {
  connectionString?: string;
  host?: string;
  port?: number;
  database?: string;
  user?: string;
  password?: string;
  max?: number;
  ssl?: boolean | object;
  skipSchema?: boolean;
}

export class PostgreSQLProvider implements StorageProvider {
  private pool: pg.Pool | null = null;
  private config: PostgreSQLProviderConfig;

  constructor(config: PostgreSQLProviderConfig = {}) {
    this.config = config;
  }

  async connect(): Promise<void> {
    const poolConfig: pg.PoolConfig = this.config.connectionString
      ? { connectionString: this.config.connectionString }
      : {
          host: this.config.host ?? 'localhost',
          port: this.config.port ?? 5432,
          database: this.config.database ?? 'ecms',
          user: this.config.user ?? 'ecms',
          password: this.config.password ?? 'ecms',
        };

    poolConfig.max = this.config.max ?? 20;

    this.pool = new Pool(poolConfig);

    const client = await this.pool.connect();
    client.release();

    if (!this.config.skipSchema) {
      await this.initializeSchema();
    }
  }

  async disconnect(): Promise<void> {
    if (this.pool) {
      await this.pool.end();
      this.pool = null;
    }
  }

  async query<T>(sql: string, params: unknown[] = []): Promise<T[]> {
    if (!this.pool) throw new Error('Database not connected');
    const pgSql = convertPlaceholders(sql);
    const result = await this.pool.query(pgSql, params as any[]);
    return result.rows.map(row => this.normalizeRow(row)) as T[];
  }

  async execute(sql: string, params: unknown[] = []): Promise<void> {
    if (!this.pool) throw new Error('Database not connected');
    const pgSql = convertPlaceholders(sql);
    await this.pool.query(pgSql, params as any[]);
  }

  // Map of lowercase PG column names → camelCase names used in code
  private static readonly COLUMN_MAP: Record<string, string> = {
    setupcomplete: 'setupComplete',
    licensekey: 'licenseKey',
    aiprovider: 'aiProvider',
    aiapikey: 'aiApiKey',
    aimodel: 'aiModel',
    passwordhash: 'passwordHash',
    ownerid: 'ownerId',
    parentid: 'parentId',
    userid: 'userId',
    expiresat: 'expiresAt',
    businessgoal: 'businessGoal',
    createdat: 'createdAt',
    updatedat: 'updatedAt',
    orgid: 'orgId',
    projectid: 'projectId',
    agentid: 'agentId',
    systemprompt: 'systemPrompt',
    storagepath: 'storagePath',
    versionhistory: 'versionHistory',
    assignedto: 'assignedTo',
    originalgoal: 'originalGoal',
  };

  private normalizeRow(row: Record<string, unknown>): Record<string, unknown> {
    const normalized: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(row)) {
      const camelKey = PostgreSQLProvider.COLUMN_MAP[key] || key;
      normalized[camelKey] = value;
    }
    return normalized;
  }

  private async initializeSchema(): Promise<void> {
    if (!this.pool) return;
    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS organization (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        domain TEXT NOT NULL,
        setupcomplete INTEGER NOT NULL DEFAULT 0,
        licensekey TEXT,
        aiprovider TEXT,
        aiapikey TEXT,
        aimodel TEXT,
        storage TEXT,
        database TEXT
      );

      CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        passwordhash TEXT NOT NULL,
        role TEXT NOT NULL,
        department TEXT,
        active INTEGER NOT NULL DEFAULT 1
      );

      CREATE TABLE IF NOT EXISTS departments (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        ownerid TEXT,
        parentid TEXT
      );

      CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        action TEXT NOT NULL,
        userid TEXT,
        details TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS auth_sessions (
        id TEXT PRIMARY KEY,
        userid TEXT NOT NULL,
        token TEXT NOT NULL,
        expiresat TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS business_projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        businessgoal TEXT,
        ownerid TEXT,
        department TEXT,
        status TEXT,
        priority TEXT,
        tags TEXT,
        createdat TEXT,
        updatedat TEXT
      );

      CREATE TABLE IF NOT EXISTS invitations (
        id TEXT PRIMARY KEY,
        orgid TEXT,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        token TEXT NOT NULL,
        expiresat TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS project_agents (
        id TEXT PRIMARY KEY,
        projectid TEXT,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        config TEXT,
        systemprompt TEXT
      );

      CREATE TABLE IF NOT EXISTS execution_nodes (
        id TEXT PRIMARY KEY,
        projectid TEXT,
        agentid TEXT,
        state TEXT NOT NULL,
        dependencies TEXT,
        outputs TEXT,
        reasoning TEXT
      );

      CREATE TABLE IF NOT EXISTS artifacts (
        id TEXT PRIMARY KEY,
        projectid TEXT,
        type TEXT NOT NULL,
        storagepath TEXT,
        versionhistory TEXT
      );

      CREATE TABLE IF NOT EXISTS human_queue (
        id TEXT PRIMARY KEY,
        projectid TEXT,
        agentid TEXT,
        reason TEXT NOT NULL,
        status TEXT NOT NULL,
        resolution TEXT,
        assignedto TEXT
      );

      CREATE TABLE IF NOT EXISTS agent_memory (
        id TEXT PRIMARY KEY,
        agentid TEXT NOT NULL,
        type TEXT NOT NULL,
        key TEXT,
        value TEXT,
        embeddings TEXT
      );

      CREATE TABLE IF NOT EXISTS general_ai_sessions (
        id TEXT PRIMARY KEY,
        projectid TEXT,
        userid TEXT NOT NULL,
        stage TEXT NOT NULL,
        originalgoal TEXT NOT NULL,
        clarification TEXT,
        summary TEXT,
        createdat TEXT NOT NULL,
        updatedat TEXT NOT NULL
      );
    `);
  }
}
