export interface KnowledgeGraphNode {
  id: string;
  label: string;
  group: string;
  category?: string;
  source_group: string | null;
  source_id?: string;
  source_url?: string;
  node_confidence: number;
  x?: number;
  y?: number;
}

export interface KnowledgeGraphEdge {
  id: string;
  source: string | KnowledgeGraphNode;
  target: string | KnowledgeGraphNode;
  label: string;
}

export function edgeEndpointId(endpoint: KnowledgeGraphEdge['source']): string {
  return typeof endpoint === 'string' ? endpoint : endpoint.id;
}
