import { Tool } from '@aegisos/contracts';

export interface IToolExecutionEngine {
  // Placeholder interface representing external engines that execute tools
  execute(tool: Tool, input: unknown): Promise<unknown>;
}

export interface IToolRepository {
  // Persistence interface for tools
  save(tool: Tool): Promise<void>;
  findById(id: string): Promise<Tool | null>;
}
