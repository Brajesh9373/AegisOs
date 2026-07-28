import { Tool } from '@aegisos/contracts';
import { ToolLifecycle } from './lifecycle.js';
import { IToolMetadata } from './metadata.js';

export class ToolContext {
  public readonly lifecycle = new ToolLifecycle();
  public metadata?: IToolMetadata;

  constructor(public readonly tool: Tool) {}
}
