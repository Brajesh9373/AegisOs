import { MemoryBase } from './registry.js';
import { MemoryLifecycle } from './lifecycle.js';
import { IMemoryMetadata } from './metadata.js';

export class MemoryContext {
  public readonly lifecycle = new MemoryLifecycle();
  public metadata?: IMemoryMetadata;

  constructor(public readonly memory: MemoryBase) {}
}
