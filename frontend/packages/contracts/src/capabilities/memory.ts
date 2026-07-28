import { z } from 'zod';
import { BaseEntitySchema } from '../core/base';

export const CacheTierSchema = z.enum(['L1', 'L2', 'L3', 'L4', 'L5']);
export type CacheTier = z.infer<typeof CacheTierSchema>;

export const MemorySnapshotSchema = BaseEntitySchema.extend({
  tier: CacheTierSchema,
  agentId: z.string().uuid(),
  contextPayload: z.string(),
  expiresAt: z.string().datetime().optional(),
});
export type MemorySnapshot = z.infer<typeof MemorySnapshotSchema>;
