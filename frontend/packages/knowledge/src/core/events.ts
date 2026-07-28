import { DomainEvent } from '@aegisos/contracts';
import { generateId } from '@aegisos/shared';

export class KnowledgeEventFactory {
  public static createKnowledgeRegisteredEvent(knowledgeId: string): DomainEvent {
    return {
      eventId: generateId(),
      eventType: 'KNOWLEDGE_REGISTERED',
      timestamp: new Date().toISOString(),
      payload: { knowledgeId },
    };
  }

  public static createKnowledgeArchivedEvent(knowledgeId: string): DomainEvent {
    return {
      eventId: generateId(),
      eventType: 'KNOWLEDGE_ARCHIVED',
      timestamp: new Date().toISOString(),
      payload: { knowledgeId },
    };
  }
}
