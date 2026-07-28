import { WorkflowNode } from './nodes.js';
import { WorkflowEdge } from './edges.js';

export class WorkflowGraph {
  public nodes: Map<string, WorkflowNode> = new Map();
  public edges: WorkflowEdge[] = [];

  public addNode(node: WorkflowNode): void {
    this.nodes.set(node.id, node);
  }

  public addEdge(edge: WorkflowEdge): void {
    this.edges.push(edge);
  }

  public getNodes(): WorkflowNode[] {
    return Array.from(this.nodes.values());
  }

  public getEdges(): WorkflowEdge[] {
    return this.edges;
  }
}
