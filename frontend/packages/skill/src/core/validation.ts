import { Skill, SkillSchema } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';

export class SkillValidationError extends PlatformError {
  constructor(message: string) {
    super(message);
  }
}

export class SkillValidator {
  public static validate(skill: unknown): Skill {
    const result = SkillSchema.safeParse(skill);
    if (!result.success) {
      throw new SkillValidationError(result.error.message);
    }
    return result.data;
  }
}
