import { KnowledgeGraphStore } from '@aegisos/knowledge';
import { CacheManager } from '../cache/manager';
import { MemoryLifecyclePolicy } from '../policies/lifecycle';

export class MemoryCoordinator {
  constructor(
    private kgStore: KnowledgeGraphStore,
    private cache: CacheManager,
    private policy: MemoryLifecyclePolicy,
  ) {}

  queryWorkingMemory(agentId: string) {
    void agentId;
    return Array.from(this.cache['cache'].get('L1')?.values() || []);
  }
  querySemanticMemory(query: string) {
    return this.kgStore.semanticQuery(query);
  }
}
