export interface ISkillMetadata {
  tags: string[];
  author: string;
  isOfficial: boolean;
  estimatedDurationMs: number;
}

export class SkillMetadataManager {
  private metadata = new Map<string, ISkillMetadata>();

  public setMetadata(skillId: string, meta: ISkillMetadata): void {
    this.metadata.set(skillId, meta);
  }

  public getMetadata(skillId: string): ISkillMetadata | undefined {
    return this.metadata.get(skillId);
  }
}
