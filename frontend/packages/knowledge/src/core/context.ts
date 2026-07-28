import { KnowledgeBase } from './registry.js';
import { KnowledgeLifecycle } from './lifecycle.js';
import { IKnowledgeMetadata } from './metadata.js';

export class KnowledgeContext {
  public readonly lifecycle = new KnowledgeLifecycle();
  public metadata?: IKnowledgeMetadata;

  constructor(public readonly knowledge: KnowledgeBase) {}
}
