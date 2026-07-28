import { ToolRegistry } from './registry.js';
import { Tool } from '@aegisos/contracts';

export class ToolRegistryAPI {
  constructor(private registry: ToolRegistry) {}

  public getTool(id: string): Tool {
    return this.registry.get(id);
  }

  public registerTool(tool: Tool): void {
    this.registry.register(tool);
  }

  public listTools(): Tool[] {
    return this.registry.getAll();
  }
}
