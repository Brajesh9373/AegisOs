import { DigitalEmployeeIdentity, WorkspaceContext } from '@aegisos/agent';
import { TraceabilityContext } from '../traceability/chain';
import { AuditLedger } from '../audit/ledger';

export class AgentExecutionContext {
  constructor(
    public identity: DigitalEmployeeIdentity,
    public workspace: WorkspaceContext,
    public traceability: TraceabilityContext,
    public audit: AuditLedger,
    public executionId: string = 'exec-' + Date.now(),
  ) {}
}
