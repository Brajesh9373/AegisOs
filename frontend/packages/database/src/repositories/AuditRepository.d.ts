import { StorageProvider } from '../core/StorageProvider.js';
export declare class AuditRepository {
    private storage;
    constructor(storage: StorageProvider);
    log(action: string, userId: string, details: string): Promise<void>;
}
