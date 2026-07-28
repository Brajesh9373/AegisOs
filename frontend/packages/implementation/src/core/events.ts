export enum ImplementationEventType {
  Registered = 'implementation.registered',
  Bound = 'implementation.bound',
  Failed = 'implementation.failed',
}

export interface ImplementationEvent {
  type: ImplementationEventType;
  implementationId: string;
  timestamp: Date;
  payload?: Record<string, unknown>;
}
