import { AgentStatus } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';

export class InvalidStateTransitionError extends PlatformError {
  constructor(from: AgentStatus, to: AgentStatus) {
    super(`Invalid state transition from ${from} to ${to}`);
  }
}

export class AgentStateMachine {
  private _status: AgentStatus = 'Idle';

  get status(): AgentStatus {
    return this._status;
  }

  public transition(newStatus: AgentStatus): void {
    const validTransitions: Record<AgentStatus, AgentStatus[]> = {
      Idle: ['Assigned', 'Archived'],
      Assigned: ['Planning', 'Idle', 'Cancelled'],
      Planning: ['Waiting', 'Executing', 'Cancelled'],
      Waiting: ['Executing', 'Cancelled'],
      Executing: ['Validating', 'Blocked', 'Failed', 'Cancelled'],
      Validating: ['Approval Pending', 'Retrying', 'Completed', 'Failed'],
      Blocked: ['Executing', 'Cancelled'],
      'Approval Pending': ['Completed', 'Retrying', 'Cancelled'],
      Retrying: ['Executing', 'Failed', 'Cancelled'],
      Completed: ['Idle', 'Archived'],
      Failed: ['Idle', 'Archived'],
      Cancelled: ['Idle', 'Archived'],
      Archived: [],
    };

    if (!validTransitions[this._status].includes(newStatus)) {
      throw new InvalidStateTransitionError(this._status, newStatus);
    }

    this._status = newStatus;
  }
}
