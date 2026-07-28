import { ExecutionContext, ExecutionState, ExecutionPolicy, ExecutionEvent } from './types.js';
import { ExecutionStateMachine } from './state-machine.js';
import { Executor } from './executors.js';
export declare class ExecutionSession {
    id: string;
    context: ExecutionContext;
    stateMachine: ExecutionStateMachine;
    constructor(id: string, traceId: string);
    updateState(state: ExecutionState): void;
}
export declare class ExecutionQueue {
    private queue;
    enqueue(session: ExecutionSession): void;
    dequeue(): ExecutionSession | undefined;
}
export declare class ExecutionDispatcher {
    dispatch(_event: ExecutionEvent): void;
}
export declare class TimeoutManager {
    enforceTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T>;
}
export declare class ExecutionPipeline {
    private executor;
    private timeoutManager;
    constructor(executor: Executor, timeoutManager: TimeoutManager);
    run(session: ExecutionSession, policy: ExecutionPolicy): Promise<void>;
}
export declare class ExecutionScheduler {
    private queue;
    private dispatcher;
    private timeoutManager;
    constructor(queue: ExecutionQueue, dispatcher: ExecutionDispatcher, timeoutManager: TimeoutManager);
    schedule(session: ExecutionSession, executor: Executor, policy: ExecutionPolicy): Promise<void>;
}
export declare class ExecutionEngine {
    private queue;
    private scheduler;
    private dispatcher;
    private timeoutManager;
    constructor();
    executePlan(executor: Executor, policy?: ExecutionPolicy): Promise<ExecutionSession>;
}
