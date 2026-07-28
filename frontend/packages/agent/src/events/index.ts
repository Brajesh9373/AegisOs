import { DomainEvent } from '@aegisos/contracts';
import { generateId } from '@aegisos/shared';

export class AgentEventFactory {
  public static createAgentStatusChanged(
    agentId: string,
    oldStatus: string,
    newStatus: string,
  ): DomainEvent {
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

  public static createAgentRegistered(agentId: string): DomainEvent {
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
