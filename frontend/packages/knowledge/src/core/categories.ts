export class KnowledgeCategoryRegistry {
  private categories = new Map<string, string[]>();

  public assignCategory(knowledgeId: string, category: string): void {
    const cats = this.categories.get(knowledgeId) || [];
    if (!cats.includes(category)) {
      cats.push(category);
      this.categories.set(knowledgeId, cats);
    }
  }

  public getCategories(knowledgeId: string): string[] {
    return this.categories.get(knowledgeId) || [];
  }
}
