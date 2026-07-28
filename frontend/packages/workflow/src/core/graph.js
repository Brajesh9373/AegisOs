export class WorkflowGraph {
    nodes = new Map();
    edges = [];
    addNode(node) {
        this.nodes.set(node.id, node);
    }
    addEdge(edge) {
        this.edges.push(edge);
    }
    getNodes() {
        return Array.from(this.nodes.values());
    }
    getEdges() {
        return this.edges;
    }
}
