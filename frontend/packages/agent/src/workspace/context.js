export class WorkspaceContext {
    identity;
    inbox = [];
    tasks = [];
    calendar = [];
    notes = [];
    approvals = [];
    reports = [];
    deliverables = [];
    constructor(identity) {
        this.identity = identity;
    }
}
