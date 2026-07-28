import { ExecutionState } from './types.js';
export class ExecutionStateMachine {
    state = ExecutionState.Created;
    validTransitions = {
        [ExecutionState.Created]: [ExecutionState.Scheduled, ExecutionState.Cancelled],
        [ExecutionState.Scheduled]: [ExecutionState.Running, ExecutionState.Cancelled],
        [ExecutionState.Running]: [
            ExecutionState.Waiting,
            ExecutionState.Paused,
            ExecutionState.Failed,
            ExecutionState.Completed,
            ExecutionState.Cancelled,
        ],
        [ExecutionState.Waiting]: [ExecutionState.Running, ExecutionState.Cancelled],
        [ExecutionState.Paused]: [ExecutionState.Running, ExecutionState.Cancelled],
        [ExecutionState.Retrying]: [
            ExecutionState.Running,
            ExecutionState.Failed,
            ExecutionState.Cancelled,
        ],
        [ExecutionState.Cancelled]: [],
        [ExecutionState.Failed]: [ExecutionState.Retrying],
        [ExecutionState.Completed]: [],
    };
    getState() {
        return this.state;
    }
    transition(newState) {
        const allowed = this.validTransitions[this.state];
        if (!allowed.includes(newState)) {
            throw new Error(`Invalid state transition from ${this.state} to ${newState}`);
        }
        this.state = newState;
    }
}
