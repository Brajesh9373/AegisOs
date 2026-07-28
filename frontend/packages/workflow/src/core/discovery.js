export class WorkflowDiscovery {
    registry;
    constructor(registry) {
        this.registry = registry;
    }
    findByName(name) {
        return this.registry.getAll().filter((k) => k.name === name);
    }
}
