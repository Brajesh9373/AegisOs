export class KnowledgeSourceRegistry {
  private sources = new Map<string, string[]>();

  public addSource(knowledgeId: string, sourceUri: string): void {
    const srcs = this.sources.get(knowledgeId) || [];
    if (!srcs.includes(sourceUri)) {
      srcs.push(sourceUri);
      this.sources.set(knowledgeId, srcs);
    }
  }

  public getSources(knowledgeId: string): string[] {
    return this.sources.get(knowledgeId) || [];
  }
}
