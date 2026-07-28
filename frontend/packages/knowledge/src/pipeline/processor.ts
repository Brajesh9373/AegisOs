import { EntityExtraction, RelationshipExtraction } from './extraction';
import { KnowledgeGraphStore } from '../graph/store';
export class KnowledgeProcessingPipeline {
  constructor(
    private store: KnowledgeGraphStore,
    private entityExt = new EntityExtraction(),
    private relExt = new RelationshipExtraction(),
  ) {}

  async process(text: string, metadata: unknown, version: number) {
    void metadata;
    const nodes = this.entityExt.extractNodes(text);
    nodes.forEach((n) => {
      n.version = version;
      this.store.addNode(n);
    });
    const edges = this.relExt.extractEdges(nodes, text);
    edges.forEach((e) => this.store.addEdge(e));
    return { nodes, edges };
  }
}
