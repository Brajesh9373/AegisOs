export enum AgentState {
  Idle = 'idle',
  Thinking = 'thinking',
  ExecutingSkill = 'executing_skill',
  ResolvingTool = 'resolving_tool',
  QueryingKnowledge = 'querying_knowledge',
  UpdatingMemory = 'updating_memory',
  WaitingForInput = 'waiting_input',
  Completed = 'completed',
  Failed = 'failed',
}

export interface AgentContextModel {
  agentId: string;
  sessionId: string;
  state: AgentState;
  memoryState: Record<string, unknown>;
  activeSkills: string[];
}

export interface AgentEvent {
  type: string;
  agentId: string;
  timestamp: number;
  payload?: unknown;
}

export interface AgentHealth {
  status: 'healthy' | 'degraded' | 'down';
  lastPing: number;
  activeSessions: number;
}

export interface AgentMetrics {
  totalInvocations: number;
  skillExecutions: number;
  toolResolutions: number;
  errorCount: number;
}
