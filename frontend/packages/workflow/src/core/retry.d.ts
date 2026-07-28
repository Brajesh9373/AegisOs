export interface RetryPolicyDefinition {
    maxRetries: number;
    initialDelaySeconds: number;
    backoffMultiplier: number;
    maxDelaySeconds?: number;
    retryableErrors?: string[];
}
