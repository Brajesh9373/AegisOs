import { TraceabilityLink } from '@aegisos/contracts';
export class TraceabilityContext {
  constructor(
    public correlationId: string,
    public requirementId: string,
  ) {}
  generateLink(step: TraceabilityLink['step'], payloadHash: string): TraceabilityLink {
    return {
      id: 'link-' + Date.now(),
      correlationId: this.correlationId,
      step,
      payloadHash,
      timestamp: new Date().toISOString(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  }
}
