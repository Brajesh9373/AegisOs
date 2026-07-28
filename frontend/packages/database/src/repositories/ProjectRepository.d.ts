import { StorageProvider } from '../core/StorageProvider.js';
export declare class ProjectRepository {
    private storage;
    constructor(storage: StorageProvider);
    create(project: Record<string, unknown>, userId: string): Promise<Record<string, unknown>>;
    getById(id: string): Promise<Record<string, unknown>>;
    getAll(): Promise<Record<string, unknown>[]>;
    update(id: string, updates: Record<string, unknown>, userId: string): Promise<void>;
    delete(id: string, userId: string): Promise<void>;
}
