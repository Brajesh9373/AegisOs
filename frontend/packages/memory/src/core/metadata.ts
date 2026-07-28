export interface IMemoryMetadata {
  tags: string[];
  author: string;
  isPublic: boolean;
  format?: string;
}

export class MemoryMetadataManager {
  private metadata = new Map<string, IMemoryMetadata>();

  public setMetadata(memoryId: string, meta: IMemoryMetadata): void {
    this.metadata.set(memoryId, meta);
  }

  public getMetadata(memoryId: string): IMemoryMetadata | undefined {
    return this.metadata.get(memoryId);
  }
}
