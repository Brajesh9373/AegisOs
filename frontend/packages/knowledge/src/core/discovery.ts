import { KnowledgeRegistry, KnowledgeBase } from './registry.js';
import { KnowledgeCategoryRegistry } from './categories.js';

export class KnowledgeDiscovery {
  constructor(
    private registry: KnowledgeRegistry,
    private categories: KnowledgeCategoryRegistry,
  ) {}

  public findByName(name: string): KnowledgeBase[] {
    return this.registry.getAll().filter((k) => k.name === name);
  }

  public findByCategory(category: string): KnowledgeBase[] {
    const result: KnowledgeBase[] = [];
    for (const k of this.registry.getAll()) {
      if (this.categories.getCategories(k.id).includes(category)) {
        result.push(k);
      }
    }
    return result;
  }
}
