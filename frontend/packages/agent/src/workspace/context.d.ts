import { DigitalEmployeeIdentity } from '../identity/digital-employee';
export declare class WorkspaceContext {
    identity: DigitalEmployeeIdentity;
    inbox: never[];
    tasks: never[];
    calendar: never[];
    notes: never[];
    approvals: never[];
    reports: never[];
    deliverables: never[];
    constructor(identity: DigitalEmployeeIdentity);
}
