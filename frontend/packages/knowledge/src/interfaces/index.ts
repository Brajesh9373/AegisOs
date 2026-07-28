import { KnowledgeBase } from '../core/registry.js';

export interface IKnowledgeRepository {
  save(item: KnowledgeBase): Promise<void>;
  findById(id: string): Promise<KnowledgeBase | null>;
}
