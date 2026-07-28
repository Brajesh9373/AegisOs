export interface IKnowledgeMetadata {
  tags: string[];
  author: string;
  isPublic: boolean;
  format?: string;
}

export class KnowledgeMetadataManager {
  private metadata = new Map<string, IKnowledgeMetadata>();

  public setMetadata(knowledgeId: string, meta: IKnowledgeMetadata): void {
    this.metadata.set(knowledgeId, meta);
  }

  public getMetadata(knowledgeId: string): IKnowledgeMetadata | undefined {
    return this.metadata.get(knowledgeId);
  }
}
