import { StorageProvider } from '../core/StorageProvider.js';
export declare class OrganizationRepository {
    private storage;
    constructor(storage: StorageProvider);
    get(): Promise<Record<string, unknown> | null>;
    clear(): Promise<void>;
    create(org: {
        id: string;
        name: string;
        domain: string;
        licenseKey: string;
        aiProvider: string;
        aiApiKey: string;
        aiModel: string;
        storage: string;
        database: string;
    }): Promise<void>;
}
