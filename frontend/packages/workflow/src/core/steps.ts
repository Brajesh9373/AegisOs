import { WorkflowNode, WorkflowNodeType } from './nodes.js';
import { RetryPolicyDefinition } from './retry.js';
import { TimeoutPolicyDefinition } from './timeout.js';

export interface WorkflowStepDefinition extends WorkflowNode {
  type: WorkflowNodeType.Step;
  stepType: string;
  stepReference: string;
  capabilityReference?: string;
  roleReference?: string;
  inputContract?: Record<string, unknown>;
  outputContract?: Record<string, unknown>;
  policies?: {
    retry?: RetryPolicyDefinition;
    timeout?: TimeoutPolicyDefinition;
  };
  stepMetadata?: Record<string, unknown>;
}
