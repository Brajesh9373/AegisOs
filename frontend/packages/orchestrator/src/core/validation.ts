import { OrchestratorBase } from './registry.js';
import { PlatformError } from '@aegisos/shared';

export class OrchestratorValidationError extends PlatformError {
  constructor(message: string) {
    super(`Orchestrator Validation Error: ${message}`);
  }
}

export class OrchestratorValidation {
  public validate(item: OrchestratorBase): void {
    if (!item.id || !item.name) {
      throw new OrchestratorValidationError('Missing required fields');
    }
  }
}
