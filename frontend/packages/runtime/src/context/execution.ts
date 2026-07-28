import { generateId } from '@aegisos/shared';

/**
 * Ephemeral context passed through the execution chain per request or job.
 */
export class ExecutionContext {
  public readonly correlationId: string;
  public readonly timestamp: string;
  public readonly metadata: Record<string, unknown>;

  constructor(metadata: Record<string, unknown> = {}, correlationId?: string) {
    this.correlationId = correlationId ?? generateId();
    this.timestamp = new Date().toISOString();
    this.metadata = Object.freeze({ ...metadata });
    Object.freeze(this);
  }

  public derive(additionalMetadata: Record<string, unknown>): ExecutionContext {
    return new ExecutionContext({ ...this.metadata, ...additionalMetadata }, this.correlationId);
  }
}
