import { z } from 'zod';

export const AIProviderConfigSchema = z.object({
  defaultModel: z.string().default('gpt-4'),
  openaiApiKey: z.string().optional(),
  anthropicApiKey: z.string().optional(),
  temperature: z.coerce.number().min(0).max(2).default(0.7),
});

export const IdentityProviderConfigSchema = z.object({
  issuer: z.string().url().optional(),
  clientId: z.string().optional(),
  clientSecret: z.string().optional(),
});

export const StorageProviderConfigSchema = z.object({
  provider: z.enum(['local', 's3', 'gcs', 'azure']).default('local'),
  bucketName: z.string().optional(),
  basePath: z.string().default('./data/storage'),
});
