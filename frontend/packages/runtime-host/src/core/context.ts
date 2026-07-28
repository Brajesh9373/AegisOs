export interface TenantContext {
  id: string;
  name: string;
}
export interface WorkspaceContext {
  id: string;
  tenantId: string;
}
export interface UserContext {
  id: string;
  roles: string[];
}
export interface SessionContext {
  id: string;
  activeSince: Date;
}
export interface RuntimeContext {
  tenant?: TenantContext;
  workspace?: WorkspaceContext;
  user?: UserContext;
  session?: SessionContext;
  executionId: string;
  correlationId: string;
}
