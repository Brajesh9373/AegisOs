import { PlatformError } from '@aegisos/shared';
export class WorkflowValidationError extends PlatformError {
    constructor(message) {
        super(`Workflow Validation Error: ${message}`);
    }
}
export class WorkflowValidation {
    validate(workflow) {
        if (!workflow.id || !workflow.name) {
            throw new WorkflowValidationError('Missing required fields');
        }
        if (!workflow.graph) {
            throw new WorkflowValidationError('Missing workflow graph');
        }
    }
}
