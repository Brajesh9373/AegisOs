import { WorkflowGraph } from './graph.js';
import { WorkflowMetadata } from './metadata.js';
import { WorkflowManifest } from './manifest.js';
export interface WorkflowDefinition {
    id: string;
    name: string;
    graph: WorkflowGraph;
    metadata: WorkflowMetadata;
    manifest: WorkflowManifest;
}
