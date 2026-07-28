export class AgentDiscovery {
    registry;
    constructor(registry) {
        this.registry = registry;
    }
    findByRole(role) {
        return this.registry.getAll().filter((agent) => agent.role === role);
    }
    findByDepartment(department) {
        return this.registry.getAll().filter((agent) => agent.department === department);
    }
    findIdleWorkers() {
        return this.registry
            .getAll()
            .filter((agent) => agent.status === 'Idle' && agent.role === 'Worker');
    }
}
