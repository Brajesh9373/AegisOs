import { z } from 'zod';
import { BaseEntitySchema, MetadataSchema } from '../core/base';

export const AuditLevelSchema = z.enum(['INFO', 'WARN', 'ERROR', 'CRITICAL', 'SECURITY']);

export const AuditEventSchema = BaseEntitySchema.extend({
  level: AuditLevelSchema,
  actorId: z.string().uuid().describe('ID of the Agent or System generating the event'),
  action: z.string(),
  resource: z.string(),
  details: MetadataSchema,
  ipAddress: z.string().optional(),
});
export type AuditEvent = z.infer<typeof AuditEventSchema>;

export const SecurityPolicySchema = BaseEntitySchema.extend({
  name: z.string(),
  description: z.string(),
  rules: z.array(z.string()),
  isActive: z.boolean(),
});
export type SecurityPolicy = z.infer<typeof SecurityPolicySchema>;

export const LedgerEntrySchema = BaseEntitySchema.extend({
  who: z.string().uuid(),
  when: z.string().datetime(),
  why: z.string(),
  inputPayloadHash: z.string(),
  outputPayloadHash: z.string(),
  knowledgeVersionHash: z.string().optional(),
  memorySnapshotId: z.string().uuid().optional(),
  evidenceSignature: z.string(),
  approvalSignature: z.string().optional(),
  durationMs: z.number().int(),
  costTokens: z.number().int().optional(),
  previousRecordHash: z.string(),
});
export type LedgerEntry = z.infer<typeof LedgerEntrySchema>;
