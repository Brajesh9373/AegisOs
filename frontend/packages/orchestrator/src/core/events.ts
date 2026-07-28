export enum OrchestratorEventType {
  PlanCreated = 'orchestrator.plan.created',
  PlanResolved = 'orchestrator.plan.resolved',
  ResolutionFailed = 'orchestrator.resolution.failed',
}

export interface OrchestratorEvent {
  type: OrchestratorEventType;
  planId: string;
  timestamp: Date;
  payload?: Record<string, unknown>;
}
