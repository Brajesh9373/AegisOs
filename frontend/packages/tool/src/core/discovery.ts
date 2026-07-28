import { ToolRegistry } from './registry.js';
import { ToolCategoryRegistry } from './categories.js';
import { Tool } from '@aegisos/contracts';

export class ToolDiscovery {
  constructor(
    private registry: ToolRegistry,
    private categories: ToolCategoryRegistry,
  ) {}

  public findByName(name: string): Tool[] {
    return this.registry.getAll().filter((tool) => tool.name === name);
  }

  public findByCategory(category: string): Tool[] {
    const result: Tool[] = [];
    for (const tool of this.registry.getAll()) {
      if (this.categories.getCategories(tool.id).includes(category)) {
        result.push(tool);
      }
    }
    return result;
  }
}
