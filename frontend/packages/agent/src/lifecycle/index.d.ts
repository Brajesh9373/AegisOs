import { AgentStatus } from '@aegisos/contracts';
import { AgentStateMachine } from '../core/state';
export declare class AgentHealth {
    isHealthy: boolean;
    lastCheck: Date;
    errors: Error[];
    reportError(error: Error): void;
    markHealthy(): void;
}
export declare class AgentMetrics {
    tasksCompleted: number;
    tasksFailed: number;
    activeTimeMs: number;
    recordTaskCompletion(): void;
    recordTaskFailure(): void;
}
export declare class AgentContext {
    readonly id: string;
    readonly stateMachine: AgentStateMachine;
    readonly health: AgentHealth;
    readonly metrics: AgentMetrics;
    constructor(id: string);
    get status(): AgentStatus;
}
