import { WorkflowDefinition } from './definition.js';
import { PlatformError } from '@aegisos/shared';
export declare class WorkflowValidationError extends PlatformError {
    constructor(message: string);
}
export declare class WorkflowValidation {
    validate(workflow: WorkflowDefinition): void;
}
