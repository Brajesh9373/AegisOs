export class ToolDependencyGraph {
  private edges = new Map<string, string[]>();

  public addDependency(toolId: string, dependencyId: string): void {
    const deps = this.edges.get(toolId) || [];
    if (!deps.includes(dependencyId)) {
      deps.push(dependencyId);
      this.edges.set(toolId, deps);
    }
  }

  public getDependencies(toolId: string): string[] {
    return this.edges.get(toolId) || [];
  }
}
