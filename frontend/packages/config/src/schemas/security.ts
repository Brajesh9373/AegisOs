import { z } from 'zod';

export const SecurityConfigSchema = z.object({
  corsOrigins: z.array(z.string()).default(['*']),
  rateLimitWindowMs: z.coerce.number().int().positive().default(60000),
  rateLimitMaxRequests: z.coerce.number().int().positive().default(100),
  jwtSecret: z.string().min(32).optional(),
});

export const FeatureFlagConfigSchema = z.record(z.string(), z.boolean()).default({});
