export enum PluginType {
  Provider = 'provider',
  Tool = 'tool',
  Knowledge = 'knowledge',
  Memory = 'memory',
  Workflow = 'workflow',
  UI = 'ui',
  Storage = 'storage',
  Authentication = 'authentication',
  Telemetry = 'telemetry',
}

export enum PluginLifecycleState {
  Install = 'install',
  Load = 'load',
  Initialize = 'initialize',
  Ready = 'ready',
  Disable = 'disable',
  Unload = 'unload',
  Remove = 'remove',
}

export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  type: PluginType;
  dependencies: Record<string, string>;
  capabilities: string[];
}

export interface PluginMetadata {
  publisher: string;
  tags: string[];
  homepage?: string;
}

export interface PluginContext {
  pluginId: string;
  tenantId: string;
  runtimeVersion: string;
}

export interface PluginInstance {
  manifest: PluginManifest;
  state: PluginLifecycleState;
  health: 'healthy' | 'degraded' | 'down';
}
