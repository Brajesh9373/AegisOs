export interface IMemoryPolicies {
  canStore(type: string): boolean;
  canEvict(id: string): boolean;
  getStorageLimit(): number;
}

export class MemoryPolicies implements IMemoryPolicies {
  public canStore(): boolean {
    return true;
  }
  public canEvict(): boolean {
    return true;
  }
  public getStorageLimit(): number {
    return 1000;
  }
}
