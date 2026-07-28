export enum OrchestratorLifecycleState {
  Idle = 'idle',
  Planning = 'planning',
  Resolving = 'resolving',
  Ready = 'ready',
  Failed = 'failed',
}

export class OrchestratorLifecycle {
  public state: OrchestratorLifecycleState = OrchestratorLifecycleState.Idle;

  public transition(newState: OrchestratorLifecycleState): void {
    this.state = newState;
  }
}
