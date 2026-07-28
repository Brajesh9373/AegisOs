import { WorkflowDefinition } from './definition.js';
import { PlatformError } from '@aegisos/shared';

export class WorkflowValidationError extends PlatformError {
  constructor(message: string) {
    super(`Workflow Validation Error: ${message}`);
  }
}

export class WorkflowValidation {
  public validate(workflow: WorkflowDefinition): void {
    if (!workflow.id || !workflow.name) {
      throw new WorkflowValidationError('Missing required fields');
    }
    if (!workflow.graph) {
      throw new WorkflowValidationError('Missing workflow graph');
    }
  }
}
