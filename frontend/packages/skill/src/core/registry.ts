import { Skill } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';

export class SkillNotFoundError extends PlatformError {
  constructor(id: string) {
    super(`Skill with ID ${id} not found`);
  }
}

export class SkillRegistry {
  private skills = new Map<string, Skill>();

  public register(skill: Skill): void {
    this.skills.set(skill.id, skill);
  }

  public get(id: string): Skill {
    const skill = this.skills.get(id);
    if (!skill) {
      throw new SkillNotFoundError(id);
    }
    return skill;
  }

  public getAll(): Skill[] {
    return Array.from(this.skills.values());
  }

  public remove(id: string): void {
    this.skills.delete(id);
  }
}
