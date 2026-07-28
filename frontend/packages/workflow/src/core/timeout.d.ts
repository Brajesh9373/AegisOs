export interface TimeoutPolicyDefinition {
    timeoutSeconds: number;
    actionOnTimeout: 'fail' | 'continue' | 'compensate';
}
