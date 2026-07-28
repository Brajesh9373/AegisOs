export interface Point {
  x: number;
  y: number;
}

export interface NodeModel {
  id: string;
  type: string;
  position: Point;
  data: Record<string, unknown>;
}

export interface EdgeModel {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  sourceHandle?: string;
  targetHandle?: string;
  type?: string;
}

export interface CanvasModel {
  nodes: NodeModel[];
  edges: EdgeModel[];
  viewport: { x: number; y: number; zoom: number };
}
