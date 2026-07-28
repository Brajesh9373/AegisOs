import { Tool } from '@aegisos/contracts';
import { generateId } from '@aegisos/shared';

export class ToolFactory {
  public static create(
    name: string,
    version: string,
    description: string,
    inputSchema: Record<string, unknown> = {},
    outputSchema: Record<string, unknown> = {},
    timeoutMs: number = 30000,
    isIdempotent: boolean = false,
    approvalRequired: boolean = false,
  ): Tool {
    return {
      id: generateId(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      name,
      version,
      description,
      inputSchema,
      outputSchema,
      timeoutMs,
      isIdempotent,
      approvalRequired,
    };
  }
}
