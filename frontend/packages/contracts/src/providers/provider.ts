import { z } from 'zod';

/** @deprecated Use Universal Connector Framework (v3.2) instead */
export const ProviderConfigSchema = z.object({
  providerId: z.string(),
  type: z.enum(['LLM', 'Database', 'Search', 'Storage']),
  endpoint: z.string().url(),
  credentialsSecretKey: z.string(),
  rateLimit: z.number().int().positive().optional(),
});
export type ProviderConfig = z.infer<typeof ProviderConfigSchema>;
