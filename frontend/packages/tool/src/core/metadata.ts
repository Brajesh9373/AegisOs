export interface IToolMetadata {
  tags: string[];
  author: string;
  isOfficial: boolean;
  rateLimitConfig?: Record<string, unknown>;
}

export class ToolMetadataManager {
  private metadata = new Map<string, IToolMetadata>();

  public setMetadata(toolId: string, meta: IToolMetadata): void {
    this.metadata.set(toolId, meta);
  }

  public getMetadata(toolId: string): IToolMetadata | undefined {
    return this.metadata.get(toolId);
  }
}
