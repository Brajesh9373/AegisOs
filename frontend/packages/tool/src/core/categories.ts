export class ToolCategoryRegistry {
  private categories = new Map<string, string[]>();

  public assignCategory(toolId: string, category: string): void {
    const cats = this.categories.get(toolId) || [];
    if (!cats.includes(category)) {
      cats.push(category);
      this.categories.set(toolId, cats);
    }
  }

  public getCategories(toolId: string): string[] {
    return this.categories.get(toolId) || [];
  }
}
