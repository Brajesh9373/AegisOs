import { Skill } from '@aegisos/contracts';
import { generateId } from '@aegisos/shared';

export class SkillFactory {
  public static create(
    name: string,
    version: string,
    description: string,
    requiredTools: string[] = [],
    inputSchema: Record<string, unknown> = {},
    outputSchema: Record<string, unknown> = {},
  ): Skill {
    return {
      id: generateId(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      name,
      version,
      description,
      requiredTools,
      inputSchema,
      outputSchema,
    };
  }
}
