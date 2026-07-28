import { WorkflowNode } from './nodes.js';
import { WorkflowEdge } from './edges.js';
export declare class WorkflowGraph {
    nodes: Map<string, WorkflowNode>;
    edges: WorkflowEdge[];
    addNode(node: WorkflowNode): void;
    addEdge(edge: WorkflowEdge): void;
    getNodes(): WorkflowNode[];
    getEdges(): WorkflowEdge[];
}
