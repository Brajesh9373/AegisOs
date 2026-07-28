import { z } from 'zod';
import { EnvironmentSchema } from '@aegisos/contracts';

export const AppConfigSchema = z.object({
  name: z.string().default('aegisOS'),
  version: z.string().default('0.1.0'),
  environment: EnvironmentSchema.default('development'),
});

export const RuntimeConfigSchema = z.object({
  logLevel: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  telemetryEnabled: z.boolean().default(true),
  gracefulShutdownMs: z.coerce.number().int().positive().default(5000),
});
