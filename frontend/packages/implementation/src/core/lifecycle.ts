export enum ImplementationLifecycleState {
  Draft = 'draft',
  Active = 'active',
  Archived = 'archived',
}

export class ImplementationLifecycle {
  public state: ImplementationLifecycleState = ImplementationLifecycleState.Draft;

  public transition(newState: ImplementationLifecycleState): void {
    this.state = newState;
  }
}
