import { Skill } from '@aegisos/contracts';
import { SkillLifecycle } from './lifecycle.js';
import { ISkillMetadata } from './metadata.js';

export class SkillContext {
  public readonly lifecycle = new SkillLifecycle();
  public metadata?: ISkillMetadata;

  constructor(public readonly skill: Skill) {}
}
