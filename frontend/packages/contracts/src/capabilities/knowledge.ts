import { z } from 'zod';
import { BaseEntitySchema, MetadataSchema } from '../core/base';

/** @deprecated Legacy vector storage */
export const MemoryAssetSchema = BaseEntitySchema.extend({
  title: z.string(),
  content: z.string(),
  source: z.string(),
  confidence: z.number().min(0).max(1),
  embeddingVectorId: z.string().optional(),
  tags: z.array(z.string()),
});
export type MemoryAsset = z.infer<typeof MemoryAssetSchema>;

export const MemoryEpisodeSchema = BaseEntitySchema.extend({
  agentId: z.string().uuid(),
  taskId: z.string().uuid(),
  context: z.string(),
  outcome: z.string(),
  timestamp: z.string().datetime(),
  metadata: MetadataSchema.optional(),
});
export type MemoryEpisode = z.infer<typeof MemoryEpisodeSchema>;

export const KnowledgeGraphNodeSchema = BaseEntitySchema.extend({
  label: z.string(),
  properties: z.record(z.any()),
});
export type KnowledgeGraphNode = z.infer<typeof KnowledgeGraphNodeSchema>;

export const KnowledgeGraphEdgeSchema = BaseEntitySchema.extend({
  sourceNodeId: z.string().uuid(),
  targetNodeId: z.string().uuid(),
  relationship: z.string(),
});
export type KnowledgeGraphEdge = z.infer<typeof KnowledgeGraphEdgeSchema>;
