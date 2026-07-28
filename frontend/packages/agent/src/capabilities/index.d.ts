import { PlatformError } from '@aegisos/shared';
export declare class CapabilityNotFoundError extends PlatformError {
    constructor(id: string);
}
export declare class AgentCapabilityRegistry {
    private capabilities;
    registerCapability(agentId: string, capabilityId: string): void;
    getCapabilities(agentId: string): string[];
    hasCapability(agentId: string, capabilityId: string): boolean;
}
