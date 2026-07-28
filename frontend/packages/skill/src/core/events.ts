import { DomainEvent } from '@aegisos/contracts';
import { generateId } from '@aegisos/shared';

export class SkillEventFactory {
  public static createSkillRegisteredEvent(skillId: string): DomainEvent {
    return {
      eventId: generateId(),
      eventType: 'SKILL_REGISTERED',
      timestamp: new Date().toISOString(),
      payload: { skillId },
    };
  }

  public static createSkillDeprecatedEvent(skillId: string): DomainEvent {
    return {
      eventId: generateId(),
      eventType: 'SKILL_DEPRECATED',
      timestamp: new Date().toISOString(),
      payload: { skillId },
    };
  }
}
