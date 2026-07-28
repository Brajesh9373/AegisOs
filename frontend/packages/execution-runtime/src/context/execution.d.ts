import { DigitalEmployeeIdentity, WorkspaceContext } from '@aegisos/agent';
import { TraceabilityContext } from '../traceability/chain';
import { AuditLedger } from '../audit/ledger';
export declare class AgentExecutionContext {
    identity: DigitalEmployeeIdentity;
    workspace: WorkspaceContext;
    traceability: TraceabilityContext;
    audit: AuditLedger;
    executionId: string;
    constructor(identity: DigitalEmployeeIdentity, workspace: WorkspaceContext, traceability: TraceabilityContext, audit: AuditLedger, executionId?: string);
}
