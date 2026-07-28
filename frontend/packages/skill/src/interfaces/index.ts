import { Skill } from '@aegisos/contracts';

export interface ISkillExecutionEngine {
  // Placeholder interface representing external engines that execute skills
  execute(skill: Skill, input: unknown): Promise<unknown>;
}

export interface ISkillRepository {
  // Persistence interface for skills
  save(skill: Skill): Promise<void>;
  findById(id: string): Promise<Skill | null>;
}
