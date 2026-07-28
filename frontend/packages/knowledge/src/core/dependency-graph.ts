export class KnowledgeDependencyGraph {
  private edges = new Map<string, string[]>();

  public addDependency(knowledgeId: string, dependencyId: string): void {
    const deps = this.edges.get(knowledgeId) || [];
    if (!deps.includes(dependencyId)) {
      deps.push(dependencyId);
      this.edges.set(knowledgeId, deps);
    }
  }

  public getDependencies(knowledgeId: string): string[] {
    return this.edges.get(knowledgeId) || [];
  }
}
