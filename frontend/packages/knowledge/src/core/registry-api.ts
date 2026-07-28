import { KnowledgeRegistry, KnowledgeBase } from './registry.js';

export class KnowledgeRegistryAPI {
  constructor(private registry: KnowledgeRegistry) {}

  public getKnowledge(id: string): KnowledgeBase {
    return this.registry.get(id);
  }

  public registerKnowledge(item: KnowledgeBase): void {
    this.registry.register(item);
  }

  public listKnowledge(): KnowledgeBase[] {
    return this.registry.getAll();
  }
}
