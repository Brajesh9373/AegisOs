export interface ProviderHealthContract {
  status: 'healthy' | 'degraded' | 'down';
  lastChecked: string;
  latencyMs?: number;
}
