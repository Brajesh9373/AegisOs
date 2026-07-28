export class KnowledgeResolver {
  public resolveKnowledge(knowledgeReference: string): string {
    return `resolved-knowledge-for-${knowledgeReference}`;
  }
}
