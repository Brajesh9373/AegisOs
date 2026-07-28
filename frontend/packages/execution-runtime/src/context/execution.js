export class AgentExecutionContext {
    identity;
    workspace;
    traceability;
    audit;
    executionId;
    constructor(identity, workspace, traceability, audit, executionId = 'exec-' + Date.now()) {
        this.identity = identity;
        this.workspace = workspace;
        this.traceability = traceability;
        this.audit = audit;
        this.executionId = executionId;
    }
}
