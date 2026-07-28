import { KnowledgeGraphNode, KnowledgeGraphEdge } from '@aegisos/contracts';
export interface NodeModel extends KnowledgeGraphNode {
  id: string;
  version: number;
  classification: string;
}
export interface EdgeModel extends KnowledgeGraphEdge {
  id: string;
  weight: number;
}
