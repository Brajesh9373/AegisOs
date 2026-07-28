export interface IMemoryRetentionRules {
  getRetentionPeriod(type: string): number;
  shouldEvict(createdAt: Date, type: string): boolean;
}

export class MemoryRetentionRules implements IMemoryRetentionRules {
  public getRetentionPeriod(): number {
    return 3600;
  }
  public shouldEvict(): boolean {
    return false;
  }
}
