import { TraceabilityLink } from '@aegisos/contracts';
export declare class TraceabilityContext {
    correlationId: string;
    requirementId: string;
    constructor(correlationId: string, requirementId: string);
    generateLink(step: TraceabilityLink['step'], payloadHash: string): TraceabilityLink;
}
