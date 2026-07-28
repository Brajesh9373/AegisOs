import { BaseEntity } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';
export interface WorkflowBase extends BaseEntity {
    name: string;
    version: string;
    description: string;
}
export declare class WorkflowNotFoundError extends PlatformError {
    constructor(id: string);
}
export declare class WorkflowRegistry {
    private items;
    register(item: WorkflowBase): void;
    get(id: string): WorkflowBase;
    getAll(): WorkflowBase[];
    remove(id: string): void;
}
