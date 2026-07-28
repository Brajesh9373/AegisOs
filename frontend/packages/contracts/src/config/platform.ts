import { z } from 'zod';

export const EnvironmentSchema = z.enum(['development', 'staging', 'production', 'test']);

export const PlatformConfigSchema = z.object({
  env: EnvironmentSchema.default('development'),
  port: z.coerce.number().int().positive().default(3000),
  logLevel: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  databaseUrl: z.string().url(),
  redisUrl: z.string().url(),
  telemetryEnabled: z.boolean().default(true),
});
export type PlatformConfig = z.infer<typeof PlatformConfigSchema>;
