import { PlatformError } from '@aegisos/shared';

export type SkillState = 'Unregistered' | 'Registered' | 'Active' | 'Deprecated';

export class InvalidSkillStateTransitionError extends PlatformError {
  constructor(from: SkillState, to: SkillState) {
    super(`Invalid skill state transition from ${from} to ${to}`);
  }
}

export class SkillLifecycle {
  private state: SkillState = 'Unregistered';

  public getState(): SkillState {
    return this.state;
  }

  public transition(newState: SkillState): void {
    const validTransitions: Record<SkillState, SkillState[]> = {
      Unregistered: ['Registered'],
      Registered: ['Active', 'Deprecated', 'Unregistered'],
      Active: ['Deprecated', 'Registered'],
      Deprecated: ['Unregistered'],
    };

    if (!validTransitions[this.state].includes(newState)) {
      throw new InvalidSkillStateTransitionError(this.state, newState);
    }
    this.state = newState;
  }
}
