import { PlatformError } from '@aegisos/shared';

export type ToolState = 'Unregistered' | 'Registered' | 'Active' | 'Deprecated';

export class InvalidToolStateTransitionError extends PlatformError {
  constructor(from: ToolState, to: ToolState) {
    super(`Invalid tool state transition from ${from} to ${to}`);
  }
}

export class ToolLifecycle {
  private state: ToolState = 'Unregistered';

  public getState(): ToolState {
    return this.state;
  }

  public transition(newState: ToolState): void {
    const validTransitions: Record<ToolState, ToolState[]> = {
      Unregistered: ['Registered'],
      Registered: ['Active', 'Deprecated', 'Unregistered'],
      Active: ['Deprecated', 'Registered'],
      Deprecated: ['Unregistered'],
    };

    if (!validTransitions[this.state].includes(newState)) {
      throw new InvalidToolStateTransitionError(this.state, newState);
    }
    this.state = newState;
  }
}
