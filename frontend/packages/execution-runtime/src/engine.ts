import { ExecutionContext, ExecutionState, ExecutionPolicy, ExecutionEvent } from './types.js';
import { ExecutionStateMachine } from './state-machine.js';
import { Executor } from './executors.js';

export class ExecutionSession {
  public id: string;
  public context: ExecutionContext;
  public stateMachine: ExecutionStateMachine;

  constructor(id: string, traceId: string) {
    this.id = id;
    this.stateMachine = new ExecutionStateMachine();
    this.context = {
      executionId: id,
      traceId,
      correlationId: `corr-${id}`,
      state: this.stateMachine.getState(),
      variables: new Map(),
      startTime: Date.now(),
    };
  }

  public updateState(state: ExecutionState): void {
    this.stateMachine.transition(state);
    this.context.state = this.stateMachine.getState();
    if (
      state === ExecutionState.Completed ||
      state === ExecutionState.Failed ||
      state === ExecutionState.Cancelled
    ) {
      this.context.endTime = Date.now();
    }
  }
}

export class ExecutionQueue {
  private queue: ExecutionSession[] = [];
  public enqueue(session: ExecutionSession): void {
    this.queue.push(session);
  }
  public dequeue(): ExecutionSession | undefined {
    return this.queue.shift();
  }
}

export class ExecutionDispatcher {
  public dispatch(_event: ExecutionEvent): void {
    // Dispatch events to telemetry, logs, or metrics systems
  }
}

export class TimeoutManager {
  public async enforceTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
    let timer: NodeJS.Timeout;
    const timeout = new Promise<never>((_, reject) => {
      timer = setTimeout(() => reject(new Error('Execution timeout exceeded')), timeoutMs);
    });
    return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
  }
}

export class ExecutionPipeline {
  constructor(
    private executor: Executor,
    private timeoutManager: TimeoutManager,
  ) {}
  public async run(session: ExecutionSession, policy: ExecutionPolicy): Promise<void> {
    const task = this.executor.execute(session.context);
    if (policy.timeoutMs) {
      await this.timeoutManager.enforceTimeout(task, policy.timeoutMs);
    } else {
      await task;
    }
  }
}

export class ExecutionScheduler {
  constructor(
    private queue: ExecutionQueue,
    private dispatcher: ExecutionDispatcher,
    private timeoutManager: TimeoutManager,
  ) {}

  public async schedule(
    session: ExecutionSession,
    executor: Executor,
    policy: ExecutionPolicy,
  ): Promise<void> {
    session.updateState(ExecutionState.Scheduled);
    this.queue.enqueue(session);

    this.dispatcher.dispatch({
      type: 'ExecutionScheduled',
      executionId: session.id,
      timestamp: Date.now(),
    });

    // In a real system, the scheduler pulls from the queue asynchronously.
    // For this abstraction, we trigger execution directly to simulate consumption.
    const activeSession = this.queue.dequeue();
    if (activeSession) {
      const pipeline = new ExecutionPipeline(executor, this.timeoutManager);
      try {
        activeSession.updateState(ExecutionState.Running);
        await pipeline.run(activeSession, policy);
        activeSession.updateState(ExecutionState.Completed);
      } catch (error) {
        activeSession.updateState(ExecutionState.Failed);
        this.dispatcher.dispatch({
          type: 'ExecutionFailed',
          executionId: activeSession.id,
          timestamp: Date.now(),
          payload: { error },
        });
      }
    }
  }
}

export class ExecutionEngine {
  private queue: ExecutionQueue;
  private scheduler: ExecutionScheduler;
  private dispatcher: ExecutionDispatcher;
  private timeoutManager: TimeoutManager;

  constructor() {
    this.queue = new ExecutionQueue();
    this.dispatcher = new ExecutionDispatcher();
    this.timeoutManager = new TimeoutManager();
    this.scheduler = new ExecutionScheduler(this.queue, this.dispatcher, this.timeoutManager);
  }

  public async executePlan(
    executor: Executor,
    policy: ExecutionPolicy = {},
  ): Promise<ExecutionSession> {
    const sessionId = `exec-${Math.random().toString(36).substring(7)}`;
    const traceId = `trace-${Date.now()}`;
    const session = new ExecutionSession(sessionId, traceId);

    await this.scheduler.schedule(session, executor, policy);
    return session;
  }
}
