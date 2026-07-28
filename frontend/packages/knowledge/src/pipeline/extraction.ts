import { NodeModel, EdgeModel } from '../graph/models';
export class EntityExtraction {
  extractNodes(text: string): NodeModel[] {
    void text;
    return [
      {
        id: 'extracted-' + Date.now(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        label: 'Entity',
        properties: {},
        version: 1,
        classification: 'AUTO',
      },
    ];
  }
}
export class RelationshipExtraction {
  extractEdges(nodes: NodeModel[], text: string): EdgeModel[] {
    void text;
    if (nodes.length < 2) return [];
    return [
      {
        id: 'edge-' + Date.now(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        sourceNodeId: nodes[0].id,
        targetNodeId: nodes[1].id,
        relationship: 'RELATED',
        weight: 1.0,
      },
    ];
  }
}
