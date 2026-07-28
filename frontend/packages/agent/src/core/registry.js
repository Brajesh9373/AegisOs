import { PlatformError } from '@aegisos/shared';
export class AgentNotFoundError extends PlatformError {
    constructor(id) {
        super(`Agent with ID ${id} not found`);
    }
}
export class AgentRegistry {
    agents = new Map();
    register(agent) {
        this.agents.set(agent.id, agent);
    }
    get(id) {
        const agent = this.agents.get(id);
        if (!agent) {
            throw new AgentNotFoundError(id);
        }
        return agent;
    }
    getAll() {
        return Array.from(this.agents.values());
    }
    remove(id) {
        this.agents.delete(id);
    }
}
