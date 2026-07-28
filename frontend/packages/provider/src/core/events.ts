export enum ProviderEventType {
  Registered = 'provider.registered',
  Initialized = 'provider.initialized',
  Failed = 'provider.failed',
}

export interface ProviderEvent {
  type: ProviderEventType;
  providerId: string;
  timestamp: Date;
  payload?: Record<string, unknown>;
}
