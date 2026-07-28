export enum ProviderLifecycleState {
  Registered = 'registered',
  Initialized = 'initialized',
  Active = 'active',
  Failed = 'failed',
}

export class ProviderLifecycle {
  public state: ProviderLifecycleState = ProviderLifecycleState.Registered;

  public transition(newState: ProviderLifecycleState): void {
    this.state = newState;
  }
}
