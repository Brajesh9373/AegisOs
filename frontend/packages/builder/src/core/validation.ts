import { CanvasModel } from './canvas.js';
import { PlatformError } from '@aegisos/shared';

export class BuilderValidationError extends PlatformError {
  constructor(message: string) {
    super(`Builder Validation Error: ${message}`);
  }
}

export class BuilderValidationEngine {
  public validate(canvas: CanvasModel): void {
    if (!canvas.nodes) {
      throw new BuilderValidationError('Canvas must contain a nodes array');
    }
    if (!canvas.edges) {
      throw new BuilderValidationError('Canvas must contain an edges array');
    }

    const nodeIds = new Set(canvas.nodes.map((n) => n.id));
    for (const edge of canvas.edges) {
      if (!nodeIds.has(edge.sourceNodeId)) {
        throw new BuilderValidationError(
          `Edge ${edge.id} references missing source node ${edge.sourceNodeId}`,
        );
      }
      if (!nodeIds.has(edge.targetNodeId)) {
        throw new BuilderValidationError(
          `Edge ${edge.id} references missing target node ${edge.targetNodeId}`,
        );
      }
    }
  }
}
