import { SkillRegistry } from './registry.js';
import { SkillCategoryRegistry } from './categories.js';
import { Skill } from '@aegisos/contracts';

export class SkillDiscovery {
  constructor(
    private registry: SkillRegistry,
    private categories: SkillCategoryRegistry,
  ) {}

  public findByName(name: string): Skill[] {
    return this.registry.getAll().filter((skill) => skill.name === name);
  }

  public findByCategory(category: string): Skill[] {
    const result: Skill[] = [];
    for (const skill of this.registry.getAll()) {
      if (this.categories.getCategories(skill.id).includes(category)) {
        result.push(skill);
      }
    }
    return result;
  }
}
