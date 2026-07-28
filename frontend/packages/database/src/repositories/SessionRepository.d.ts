import { StorageProvider } from '../core/StorageProvider.js';
export declare class SessionRepository {
    private storage;
    constructor(storage: StorageProvider);
    create(id: string, userId: string, token: string, expiresAt: string): Promise<void>;
    getByToken(token: string): Promise<Record<string, unknown> | null>;
    deleteByToken(token: string): Promise<void>;
}
