import { DomainEvent } from '@aegisos/contracts';
export declare class AgentEventFactory {
    static createAgentStatusChanged(agentId: string, oldStatus: string, newStatus: string): DomainEvent;
    static createAgentRegistered(agentId: string): DomainEvent;
}
