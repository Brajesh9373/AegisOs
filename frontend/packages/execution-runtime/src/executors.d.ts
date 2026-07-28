import { ExecutionContext } from './types.js';
export interface Executor {
    execute(context: ExecutionContext): Promise<void>;
}
export declare class StepExecutor implements Executor {
    execute(_context: ExecutionContext): Promise<void>;
}
export declare class SequentialExecutor implements Executor {
    private steps;
    constructor(steps: Executor[]);
    execute(context: ExecutionContext): Promise<void>;
}
export declare class ParallelExecutor implements Executor {
    private steps;
    constructor(steps: Executor[]);
    execute(context: ExecutionContext): Promise<void>;
}
export declare class ConditionalExecutor implements Executor {
    private condition;
    private onTrue;
    private onFalse;
    constructor(condition: (ctx: ExecutionContext) => boolean, onTrue: Executor, onFalse: Executor);
    execute(context: ExecutionContext): Promise<void>;
}
export declare class RetryExecutor implements Executor {
    private step;
    private maxRetries;
    constructor(step: Executor, maxRetries: number);
    execute(context: ExecutionContext): Promise<void>;
}
export declare class CompensationExecutor implements Executor {
    private forward;
    private compensate;
    constructor(forward: Executor, compensate: Executor);
    execute(context: ExecutionContext): Promise<void>;
}
export declare class RollbackExecutor implements Executor {
    private step;
    private rollback;
    constructor(step: Executor, rollback: Executor);
    execute(context: ExecutionContext): Promise<void>;
}
