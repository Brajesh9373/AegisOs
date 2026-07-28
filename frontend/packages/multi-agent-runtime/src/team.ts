import { AgentRuntime } from '@aegisos/agent-runtime';
import {
  TeamState,
  TeamMetrics,
  SupervisorPolicy,
  SharedMemoryLayer,
  SharedKnowledgeLayer,
  TaskModel,
} from './types.js';
import { AgentPool } from './pool.js';
import { TeamManager } from './manager.js';

class InMemorySharedLayer implements SharedMemoryLayer, SharedKnowledgeLayer {
  private data = new Map<string, unknown>();

  public get(key: string): unknown {
    return this.data.get(key);
  }
  public set(key: string, value: unknown): void {
    this.data.set(key, value);
  }
  public async query(_domain: string, _params: unknown): Promise<unknown> {
    return null;
  }
}

export class TeamRuntime {
  private state: TeamState = TeamState.Forming;
  private pool: AgentPool;
  private manager: TeamManager;
  private memory = new InMemorySharedLayer();

  public metrics: TeamMetrics = {
    tasksDistributed: 0,
    tasksCompleted: 0,
    escalationsCount: 0,
    conflictsResolved: 0,
  };

  constructor(
    runtime: AgentRuntime,
    policy: SupervisorPolicy = {
      maxEscalations: 3,
      autoResolveConflicts: true,
      delegationStrategy: 'round-robin',
    },
  ) {
    this.pool = new AgentPool(runtime);
    this.manager = new TeamManager(this.pool, policy, this.memory, this.memory);
  }

  public addMember(agentId: string): void {
    this.pool.registerAgent(agentId);
  }

  public startCollaboration(): void {
    this.state = TeamState.Collaborating;
  }

  public delegate(task: TaskModel): string {
    if (this.state !== TeamState.Collaborating) throw new Error('Team is not ready to collaborate');
    this.metrics.tasksDistributed++;
    return this.manager.distributeTask(task);
  }

  public escalateTask(taskId: string, error: unknown): void {
    this.metrics.escalationsCount++;
    this.state = TeamState.Escalated;
    this.manager.escalate(taskId, error);
  }

  public complete(): void {
    this.state = TeamState.Completed;
  }

  public getState(): TeamState {
    return this.state;
  }
}
