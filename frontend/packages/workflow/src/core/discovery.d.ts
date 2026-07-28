import { WorkflowRegistry, WorkflowBase } from './registry.js';
export declare class WorkflowDiscovery {
    private registry;
    constructor(registry: WorkflowRegistry);
    findByName(name: string): WorkflowBase[];
}
