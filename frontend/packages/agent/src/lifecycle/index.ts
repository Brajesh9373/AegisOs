import { AgentStatus } from '@aegisos/contracts';
import { AgentStateMachine } from '../core/state';

export class AgentHealth {
  public isHealthy: boolean = true;
  public lastCheck: Date = new Date();
  public errors: Error[] = [];

  public reportError(error: Error): void {
    this.isHealthy = false;
    this.errors.push(error);
  }

  public markHealthy(): void {
    this.isHealthy = true;
    this.errors = [];
    this.lastCheck = new Date();
  }
}

export class AgentMetrics {
  public tasksCompleted: number = 0;
  public tasksFailed: number = 0;
  public activeTimeMs: number = 0;

  public recordTaskCompletion(): void {
    this.tasksCompleted++;
  }

  public recordTaskFailure(): void {
    this.tasksFailed++;
  }
}

export class AgentContext {
  public readonly id: string;
  public readonly stateMachine: AgentStateMachine;
  public readonly health: AgentHealth;
  public readonly metrics: AgentMetrics;

  constructor(id: string) {
    this.id = id;
    this.stateMachine = new AgentStateMachine();
    this.health = new AgentHealth();
    this.metrics = new AgentMetrics();
  }

  public get status(): AgentStatus {
    return this.stateMachine.status;
  }
}
