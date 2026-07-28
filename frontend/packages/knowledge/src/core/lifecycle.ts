import { PlatformError } from '@aegisos/shared';

export type KnowledgeState = 'Draft' | 'Published' | 'Archived';

export class InvalidKnowledgeStateTransitionError extends PlatformError {
  constructor(from: KnowledgeState, to: KnowledgeState) {
    super(`Invalid knowledge state transition from ${from} to ${to}`);
  }
}

export class KnowledgeLifecycle {
  private state: KnowledgeState = 'Draft';

  public getState(): KnowledgeState {
    return this.state;
  }

  public transition(newState: KnowledgeState): void {
    const validTransitions: Record<KnowledgeState, KnowledgeState[]> = {
      Draft: ['Published', 'Archived'],
      Published: ['Archived', 'Draft'],
      Archived: ['Draft'],
    };

    if (!validTransitions[this.state].includes(newState)) {
      throw new InvalidKnowledgeStateTransitionError(this.state, newState);
    }
    this.state = newState;
  }
}
