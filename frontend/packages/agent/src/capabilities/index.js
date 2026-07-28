import { PlatformError } from '@aegisos/shared';
export class CapabilityNotFoundError extends PlatformError {
    constructor(id) {
        super(`Capability with ID ${id} not found`);
    }
}
export class AgentCapabilityRegistry {
    capabilities = new Map();
    registerCapability(agentId, capabilityId) {
        const caps = this.capabilities.get(agentId) || [];
        if (!caps.includes(capabilityId)) {
            caps.push(capabilityId);
            this.capabilities.set(agentId, caps);
        }
    }
    getCapabilities(agentId) {
        return this.capabilities.get(agentId) || [];
    }
    hasCapability(agentId, capabilityId) {
        const caps = this.capabilities.get(agentId) || [];
        return caps.includes(capabilityId);
    }
}
