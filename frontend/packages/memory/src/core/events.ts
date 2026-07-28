import { DomainEvent } from '@aegisos/contracts';
import { generateId } from '@aegisos/shared';

export class MemoryEventFactory {
  public static createMemoryRegisteredEvent(memoryId: string): DomainEvent {
    return {
      eventId: generateId(),
      eventType: 'MEMORY_REGISTERED',
      timestamp: new Date().toISOString(),
      payload: { memoryId },
    };
  }

  public static createMemoryArchivedEvent(memoryId: string): DomainEvent {
    return {
      eventId: generateId(),
      eventType: 'MEMORY_ARCHIVED',
      timestamp: new Date().toISOString(),
      payload: { memoryId },
    };
  }
}
