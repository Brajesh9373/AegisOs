import { StorageProvider } from '../core/StorageProvider.js';
export declare class SQLiteProvider implements StorageProvider {
    private db;
    private dbPath;
    constructor(filename?: string);
    connect(): Promise<void>;
    disconnect(): Promise<void>;
    query<T>(sql: string, params?: unknown[]): Promise<T[]>;
    execute(sql: string, params?: unknown[]): Promise<void>;
    private persist;
    private initializeSchema;
}
