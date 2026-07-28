import { NodeModel, EdgeModel } from './models';
export class KnowledgeGraphStore {
  private nodes = new Map<string, NodeModel>();
  private edges = new Map<string, EdgeModel>();

  addNode(node: NodeModel) {
    this.nodes.set(node.id, node);
  }
  addEdge(edge: EdgeModel) {
    this.edges.set(edge.id, edge);
  }
  getNode(id: string) {
    return this.nodes.get(id);
  }

  traverse(startNodeId: string, depth: number = 1): NodeModel[] {
    void depth;
    return [this.nodes.get(startNodeId)].filter(Boolean) as NodeModel[];
  }

  semanticQuery(query: string) {
    void query;
    return Array.from(this.nodes.values());
  }
}
