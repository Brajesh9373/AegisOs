export class SkillCategoryRegistry {
  private categories = new Map<string, string[]>();

  public assignCategory(skillId: string, category: string): void {
    const cats = this.categories.get(skillId) || [];
    if (!cats.includes(category)) {
      cats.push(category);
      this.categories.set(skillId, cats);
    }
  }

  public getCategories(skillId: string): string[] {
    return this.categories.get(skillId) || [];
  }
}
