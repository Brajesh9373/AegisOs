import { Tool } from '@aegisos/contracts';
import { PlatformError } from '@aegisos/shared';

export class ToolNotFoundError extends PlatformError {
  constructor(id: string) {
    super(`Tool with ID ${id} not found`);
  }
}

export class ToolRegistry {
  private tools = new Map<string, Tool>();

  public register(tool: Tool): void {
    this.tools.set(tool.id, tool);
  }

  public get(id: string): Tool {
    const tool = this.tools.get(id);
    if (!tool) {
      throw new ToolNotFoundError(id);
    }
    return tool;
  }

  public getAll(): Tool[] {
    return Array.from(this.tools.values());
  }

  public remove(id: string): void {
    this.tools.delete(id);
  }
}
