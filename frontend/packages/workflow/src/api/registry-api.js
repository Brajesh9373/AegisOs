export class WorkflowRegistryAPI {
    registry;
    constructor(registry) {
        this.registry = registry;
    }
    registerWorkflow(workflow) {
        this.registry.register(workflow);
    }
    getWorkflow(id) {
        return this.registry.get(id);
    }
    listWorkflows() {
        return this.registry.getAll();
    }
}
