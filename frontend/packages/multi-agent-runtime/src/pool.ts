import { AgentRuntime, AgentSession } from '@aegisos/agent-runtime';

export class AgentPool {
  private activeAgents = new Map<string, AgentSession>();

  constructor(private runtime: AgentRuntime) {}

  public registerAgent(agentId: string): AgentSession {
    const session = this.runtime.createSession(agentId);
    this.activeAgents.set(agentId, session);
    return session;
  }

  public getAgent(agentId: string): AgentSession | undefined {
    return this.activeAgents.get(agentId);
  }

  public getAvailableAgents(): string[] {
    // Abstract availability checks
    return Array.from(this.activeAgents.keys());
  }

  public removeAgent(agentId: string): void {
    this.activeAgents.delete(agentId);
  }
}
