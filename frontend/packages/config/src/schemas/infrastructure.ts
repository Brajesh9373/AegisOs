import { z } from 'zod';

export const DatabaseConfigSchema = z.object({
  url: z.string().url().optional(),
  poolMin: z.coerce.number().int().min(1).default(2),
  poolMax: z.coerce.number().int().min(1).default(10),
});

export const QueueConfigSchema = z.object({
  redisUrl: z.string().url().optional(),
  concurrency: z.coerce.number().int().positive().default(5),
});

export const CacheConfigSchema = z.object({
  enabled: z.boolean().default(true),
  ttlSeconds: z.coerce.number().int().positive().default(3600),
  redisUrl: z.string().url().optional(),
});
