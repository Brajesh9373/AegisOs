export interface CompensationDefinition {
    targetNodeId: string;
    compensationAction: string;
    parameters: Record<string, unknown>;
}
