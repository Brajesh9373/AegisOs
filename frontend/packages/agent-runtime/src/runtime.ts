import { AgentSession } from './session.js';
import { AgentState, AgentMetrics, AgentEvent, AgentHealth } from './types.js';
import { ExecutionEngine, StepExecutor, ExecutionContext } from '@aegisos/execution-runtime';

export class AgentSkillExecutor extends StepExecutor {
  constructor(
    private skillId: string,
    private session: AgentSession,
  ) {
    super();
  }
  public async execute(_context: ExecutionContext): Promise<void> {
    this.session.updateState(AgentState.ExecutingSkill);
    // Abstract skill invocation boundaries mapping down
    this.session.updateState(AgentState.Thinking);
  }
}

export class AgentToolResolver extends StepExecutor {
  constructor(
    private toolId: string,
    private session: AgentSession,
  ) {
    super();
  }
  public async execute(_context: ExecutionContext): Promise<void> {
    this.session.updateState(AgentState.ResolvingTool);
    // Abstract tool resolution using Provider Framework natively
    this.session.updateState(AgentState.Thinking);
  }
}

export class AgentKnowledgeResolver extends StepExecutor {
  constructor(
    private query: string,
    private session: AgentSession,
  ) {
    super();
  }
  public async execute(_context: ExecutionContext): Promise<void> {
    this.session.updateState(AgentState.QueryingKnowledge);
    // Knowledge isolation layer
    this.session.updateState(AgentState.Thinking);
  }
}

export class AgentMemoryResolver extends StepExecutor {
  constructor(
    private keys: string[],
    private session: AgentSession,
  ) {
    super();
  }
  public async execute(_context: ExecutionContext): Promise<void> {
    this.session.updateState(AgentState.UpdatingMemory);
    // Memory contextual mapping
    this.session.updateState(AgentState.Thinking);
  }
}

export class AgentSupervisor {
  public validate(_session: AgentSession): void {
    // Abstract sanity checks, infinite loop protections
  }
}

export class AgentScheduler {
  constructor(
    private engine: ExecutionEngine,
    private supervisor: AgentSupervisor,
  ) {}

  public async scheduleTask(session: AgentSession, task: StepExecutor): Promise<void> {
    this.supervisor.validate(session);
    await this.engine.executePlan(task);
  }
}

export class AgentRuntime {
  private activeSessions = new Map<string, AgentSession>();
  private metrics: AgentMetrics = {
    totalInvocations: 0,
    skillExecutions: 0,
    toolResolutions: 0,
    errorCount: 0,
  };

  private engine = new ExecutionEngine();
  private supervisor = new AgentSupervisor();
  private scheduler = new AgentScheduler(this.engine, this.supervisor);

  public createSession(agentId: string): AgentSession {
    const session = new AgentSession(agentId);
    this.activeSessions.set(session.id, session);
    return session;
  }

  public async invokeSkill(sessionId: string, skillId: string): Promise<void> {
    const session = this.activeSessions.get(sessionId);
    if (!session) throw new Error('Session not found');

    this.metrics.totalInvocations++;
    this.metrics.skillExecutions++;

    try {
      await this.scheduler.scheduleTask(session, new AgentSkillExecutor(skillId, session));
    } catch (e) {
      this.metrics.errorCount++;
      session.updateState(AgentState.Failed);
      throw e;
    }
  }

  public emitEvent(_event: AgentEvent): void {
    // Pipeline for lifecycle hooks
  }

  public getHealth(): AgentHealth {
    return {
      status: 'healthy',
      lastPing: Date.now(),
      activeSessions: this.activeSessions.size,
    };
  }
}
