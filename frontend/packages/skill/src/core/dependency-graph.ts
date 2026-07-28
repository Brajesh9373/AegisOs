export class SkillDependencyGraph {
  private edges = new Map<string, string[]>();

  public addDependency(skillId: string, dependencyId: string): void {
    const deps = this.edges.get(skillId) || [];
    if (!deps.includes(dependencyId)) {
      deps.push(dependencyId);
      this.edges.set(skillId, deps);
    }
  }

  public getDependencies(skillId: string): string[] {
    return this.edges.get(skillId) || [];
  }

  public resolveOrder(skillIds: string[]): string[] {
    // Topological sort (simplified for foundation)
    const result: string[] = [];
    const visited = new Set<string>();

    const visit = (id: string) => {
      if (visited.has(id)) return;
      visited.add(id);
      const deps = this.getDependencies(id);
      for (const dep of deps) {
        visit(dep);
      }
      result.push(id);
    };

    for (const id of skillIds) {
      visit(id);
    }
    return result;
  }
}
