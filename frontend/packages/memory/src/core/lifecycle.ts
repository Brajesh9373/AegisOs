import { PlatformError } from '@aegisos/shared';

export type MemoryState = 'Draft' | 'Published' | 'Archived';

export class InvalidMemoryStateTransitionError extends PlatformError {
  constructor(from: MemoryState, to: MemoryState) {
    super(`Invalid memory state transition from ${from} to ${to}`);
  }
}

export class MemoryLifecycle {
  private state: MemoryState = 'Draft';

  public getState(): MemoryState {
    return this.state;
  }

  public transition(newState: MemoryState): void {
    const validTransitions: Record<MemoryState, MemoryState[]> = {
      Draft: ['Published', 'Archived'],
      Published: ['Archived', 'Draft'],
      Archived: ['Draft'],
    };

    if (!validTransitions[this.state].includes(newState)) {
      throw new InvalidMemoryStateTransitionError(this.state, newState);
    }
    this.state = newState;
  }
}
