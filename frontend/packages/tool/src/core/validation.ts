import { Tool, ToolSchema } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';

export class ToolValidationError extends PlatformError {
  constructor(message: string) {
    super(message);
  }
}

export class ToolValidator {
  public static validate(tool: unknown): Tool {
    const result = ToolSchema.safeParse(tool);
    if (!result.success) {
      throw new ToolValidationError(result.error.message);
    }
    return result.data;
  }
}
