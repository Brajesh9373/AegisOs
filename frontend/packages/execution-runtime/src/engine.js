import { ExecutionState } from './types.js';
import { ExecutionStateMachine } from './state-machine.js';
export class ExecutionSession {
    id;
    context;
    stateMachine;
    constructor(id, traceId) {
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
    updateState(state) {
        this.stateMachine.transition(state);
        this.context.state = this.stateMachine.getState();
        if (state === ExecutionState.Completed ||
            state === ExecutionState.Failed ||
            state === ExecutionState.Cancelled) {
            this.context.endTime = Date.now();
        }
    }
}
export class ExecutionQueue {
    queue = [];
    enqueue(session) {
        this.queue.push(session);
    }
    dequeue() {
        return this.queue.shift();
    }
}
export class ExecutionDispatcher {
    dispatch(_event) {
        // Dispatch events to telemetry, logs, or metrics systems
    }
}
export class TimeoutManager {
    async enforceTimeout(promise, timeoutMs) {
        let timer;
        const timeout = new Promise((_, reject) => {
            timer = setTimeout(() => reject(new Error('Execution timeout exceeded')), timeoutMs);
        });
        return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
    }
}
export class ExecutionPipeline {
    executor;
    timeoutManager;
    constructor(executor, timeoutManager) {
        this.executor = executor;
        this.timeoutManager = timeoutManager;
    }
    async run(session, policy) {
        const task = this.executor.execute(session.context);
        if (policy.timeoutMs) {
            await this.timeoutManager.enforceTimeout(task, policy.timeoutMs);
        }
        else {
            await task;
        }
    }
}
export class ExecutionScheduler {
    queue;
    dispatcher;
    timeoutManager;
    constructor(queue, dispatcher, timeoutManager) {
        this.queue = queue;
        this.dispatcher = dispatcher;
        this.timeoutManager = timeoutManager;
    }
    async schedule(session, executor, policy) {
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
            }
            catch (error) {
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
    queue;
    scheduler;
    dispatcher;
    timeoutManager;
    constructor() {
        this.queue = new ExecutionQueue();
        this.dispatcher = new ExecutionDispatcher();
        this.timeoutManager = new TimeoutManager();
        this.scheduler = new ExecutionScheduler(this.queue, this.dispatcher, this.timeoutManager);
    }
    async executePlan(executor, policy = {}) {
        const sessionId = `exec-${Math.random().toString(36).substring(7)}`;
        const traceId = `trace-${Date.now()}`;
        const session = new ExecutionSession(sessionId, traceId);
        await this.scheduler.schedule(session, executor, policy);
        return session;
    }
}
