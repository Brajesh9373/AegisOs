import { AgentContextModel, AgentState } from './types.js';
import { AgentStateMachine } from './state-machine.js';

export class AgentSession {
  public id: string;
  private stateMachine: AgentStateMachine;
  private context: AgentContextModel;

  constructor(agentId: string) {
    this.id = `sess-${Math.random().toString(36).substring(7)}`;
    this.stateMachine = new AgentStateMachine();

    this.context = {
      agentId,
      sessionId: this.id,
      state: this.stateMachine.getState(),
      memoryState: {},
      activeSkills: [],
    };
  }

  public getContext(): AgentContextModel {
    return this.context;
  }

  public updateState(newState: AgentState): void {
    this.stateMachine.transition(newState);
    this.context.state = this.stateMachine.getState();
  }
}
