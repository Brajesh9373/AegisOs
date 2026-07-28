import { WorkflowRegistry, WorkflowBase } from '../core/registry.js';
export declare class WorkflowRegistryAPI {
    private registry;
    constructor(registry: WorkflowRegistry);
    registerWorkflow(workflow: WorkflowBase): void;
    getWorkflow(id: string): WorkflowBase;
    listWorkflows(): WorkflowBase[];
}
