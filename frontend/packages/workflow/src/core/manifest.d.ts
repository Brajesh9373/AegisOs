export interface WorkflowManifest {
    id: string;
    name: string;
    version: string;
    metadata: Record<string, unknown>;
}
