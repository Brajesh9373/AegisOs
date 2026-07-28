export class TraceabilityContext {
    correlationId;
    requirementId;
    constructor(correlationId, requirementId) {
        this.correlationId = correlationId;
        this.requirementId = requirementId;
    }
    generateLink(step, payloadHash) {
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
