import { AgentState } from './types.js';

export class AgentStateMachine {
  private state: AgentState = AgentState.Idle;

  private validTransitions: Record<AgentState, AgentState[]> = {
    [AgentState.Idle]: [AgentState.Thinking, AgentState.WaitingForInput],
    [AgentState.Thinking]: [
      AgentState.ExecutingSkill,
      AgentState.ResolvingTool,
      AgentState.QueryingKnowledge,
      AgentState.UpdatingMemory,
      AgentState.Completed,
      AgentState.Failed,
    ],
    [AgentState.ExecutingSkill]: [AgentState.Thinking, AgentState.Failed],
    [AgentState.ResolvingTool]: [AgentState.Thinking, AgentState.Failed],
    [AgentState.QueryingKnowledge]: [AgentState.Thinking, AgentState.Failed],
    [AgentState.UpdatingMemory]: [AgentState.Thinking, AgentState.Failed],
    [AgentState.WaitingForInput]: [AgentState.Thinking, AgentState.Failed],
    [AgentState.Completed]: [],
    [AgentState.Failed]: [AgentState.Idle],
  };

  public getState(): AgentState {
    return this.state;
  }

  public transition(newState: AgentState): void {
    const allowed = this.validTransitions[this.state];
    if (!allowed.includes(newState)) {
      throw new Error(`Invalid agent state transition from ${this.state} to ${newState}`);
    }
    this.state = newState;
  }
}
