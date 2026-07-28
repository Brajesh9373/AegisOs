import { StorageProvider } from '../core/StorageProvider.js';
export declare class UserRepository {
    private storage;
    constructor(storage: StorageProvider);
    create(user: Record<string, unknown>): Promise<void>;
    clear(): Promise<void>;
    getByEmail(email: string): Promise<Record<string, unknown>>;
    getById(id: string): Promise<Record<string, unknown>>;
    getAll(): Promise<Record<string, unknown>[]>;
    update(id: string, updates: Record<string, unknown>): Promise<void>;
}
