import { z } from 'zod';
import { BaseEntitySchema } from '../core/base';

export const SyncModalitySchema = z.enum(['Batch', 'Incremental', 'Streaming', 'Webhook']);
export type SyncModality = z.infer<typeof SyncModalitySchema>;

export const ConnectorStateSchema = z.enum([
  'REGISTERED',
  'CONFIGURED',
  'VALIDATED',
  'CONNECTED',
  'SYNCHRONIZING',
  'PAUSED',
  'DISCONNECTED',
  'ARCHIVED',
]);
export type ConnectorState = z.infer<typeof ConnectorStateSchema>;

export const UniversalConnectorSchema = BaseEntitySchema.extend({
  name: z.string(),
  version: z.string(),
  state: ConnectorStateSchema,
  supportedModalities: z.array(SyncModalitySchema),
  rateLimitTokensPerMinute: z.number().int().positive().optional(),
});
export type UniversalConnector = z.infer<typeof UniversalConnectorSchema>;
