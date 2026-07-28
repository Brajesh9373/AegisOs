import { AgentStatus } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';
export declare class InvalidStateTransitionError extends PlatformError {
    constructor(from: AgentStatus, to: AgentStatus);
}
export declare class AgentStateMachine {
    private _status;
    get status(): AgentStatus;
    transition(newStatus: AgentStatus): void;
}
