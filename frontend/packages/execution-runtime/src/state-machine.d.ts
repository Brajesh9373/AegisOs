import { ExecutionState } from './types.js';
export declare class ExecutionStateMachine {
    private state;
    private validTransitions;
    getState(): ExecutionState;
    transition(newState: ExecutionState): void;
}
