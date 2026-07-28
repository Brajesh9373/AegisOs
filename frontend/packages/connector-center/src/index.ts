import { IdentityContext, SecurityEngine } from '@aegisos/security';
import { Task, UniversalConnector, AuditEvent } from '@aegisos/contracts';

export interface ConnectorCenterDTO {
  installedConnectors: UniversalConnector[];
  availableConnectors: UniversalConnector[];
  syncJobs: Task[];
  healthMetrics: Record<string, number>;
}

export interface ConnectorCenterQueryAPI {
  getCenterState(identity: IdentityContext): ConnectorCenterDTO;
  triggerSync(identity: IdentityContext, _connectorId: string): Promise<Task>;
  getConnectorLogs(identity: IdentityContext, _connectorId: string): Promise<AuditEvent[]>;
}

export class ConnectorCenterService implements ConnectorCenterQueryAPI {
  constructor(private security: SecurityEngine) {}

  private validateSecurity(identity: IdentityContext, action: string) {
    const isAuthorized = this.security.evaluateAccess(identity, 'connector-center', action);
    if (!isAuthorized) throw new Error('Unauthorized');
  }

  getCenterState(identity: IdentityContext): ConnectorCenterDTO {
    this.validateSecurity(identity, 'read');
    return {
      installedConnectors: [],
      availableConnectors: [],
      syncJobs: [],
      healthMetrics: {
        uptime: 99.9,
        successRate: 98.5,
      },
    };
  }

  async triggerSync(identity: IdentityContext, connectorId: string): Promise<Task> {
    this.validateSecurity(identity, 'execute');
    return {
      id: 'sync-' + Date.now(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      status: 'Running',
      workflowId: 'sync-wf',
      skillId: connectorId,
      retryCount: 0,
      dependencies: [],
    };
  }

  async getConnectorLogs(identity: IdentityContext, _connectorId: string): Promise<AuditEvent[]> {
    this.validateSecurity(identity, 'read');
    return [
      {
        id: 'log-1',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        resource: 'connector',
        level: 'INFO',
        actorId: 'system',
        action: 'SYNC_STARTED',
        details: { message: 'Sync started successfully', outcome: 'SUCCESS' },
      },
    ];
  }
}

export * from './ui/ConnectorCenter';
