export interface WorkflowContext {
    workflowId: string;
    runId: string;
    variables: Record<string, unknown>;
    startTime: Date;
}
