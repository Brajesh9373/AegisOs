export interface OrchestratorContext {
  planId: string;
  workflowId: string;
  variables: Record<string, unknown>;
  state: string;
}
