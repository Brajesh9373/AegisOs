import { DomainEvent } from '@aegisos/contracts';
import { generateId } from '@aegisos/shared';

export class ToolEventFactory {
  public static createToolRegisteredEvent(toolId: string): DomainEvent {
    return {
      eventId: generateId(),
      eventType: 'TOOL_REGISTERED',
      timestamp: new Date().toISOString(),
      payload: { toolId },
    };
  }

  public static createToolDeprecatedEvent(toolId: string): DomainEvent {
    return {
      eventId: generateId(),
      eventType: 'TOOL_DEPRECATED',
      timestamp: new Date().toISOString(),
      payload: { toolId },
    };
  }
}
