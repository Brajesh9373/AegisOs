import { MemoryCoordinator } from '@aegisos/memory';
import { KnowledgeGraphStore } from '@aegisos/knowledge';
export class RuntimeV3Adapter {
  constructor(
    public memory: MemoryCoordinator,
    public knowledge: KnowledgeGraphStore,
  ) {}
}
