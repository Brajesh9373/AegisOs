export enum HostState {
  Startup = 'startup',
  Ready = 'ready',
  Running = 'running',
  Paused = 'paused',
  Stopped = 'stopped',
  Shutdown = 'shutdown',
}

export class HostLifecycle {
  public state: HostState = HostState.Startup;
  private stateListeners: Array<(state: HostState) => void> = [];

  public transition(newState: HostState): void {
    if (this.state === newState) return;
    this.state = newState;
    this.stateListeners.forEach((listener) => listener(newState));
  }

  public onTransition(listener: (state: HostState) => void): void {
    this.stateListeners.push(listener);
  }
}
