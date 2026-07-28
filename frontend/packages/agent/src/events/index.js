import { generateId } from '@aegisos/shared';
export class AgentEventFactory {
    static createAgentStatusChanged(agentId, oldStatus, newStatus) {
        return {
            eventId: generateId(),
            eventType: 'AgentStatusChanged',
            timestamp: new Date().toISOString(),
            payload: {
                agentId,
                oldStatus,
                newStatus,
            },
        };
    }
    static createAgentRegistered(agentId) {
        return {
            eventId: generateId(),
            eventType: 'AgentRegistered',
            timestamp: new Date().toISOString(),
            payload: {
                agentId,
            },
        };
    }
}
