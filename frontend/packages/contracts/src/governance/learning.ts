import { z } from 'zod';
import { BaseEntitySchema } from '../core/base';

export const KnowledgeCandidateSchema = BaseEntitySchema.extend({
  traceabilityId: z.string().uuid(),
  proposedNode: z.any(), // Represents the KG Node
  humanOwnerId: z.string().uuid(),
  status: z.enum(['PENDING', 'APPROVED', 'REJECTED']),
  approvalSignature: z.string().optional(),
});
export type KnowledgeCandidate = z.infer<typeof KnowledgeCandidateSchema>;
