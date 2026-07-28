import { z } from 'zod';
import { AppConfigSchema, RuntimeConfigSchema } from './app';
import {
  AIProviderConfigSchema,
  IdentityProviderConfigSchema,
  StorageProviderConfigSchema,
} from './providers';
import { DatabaseConfigSchema, QueueConfigSchema, CacheConfigSchema } from './infrastructure';
import { SecurityConfigSchema, FeatureFlagConfigSchema } from './security';
import { DeepReadonly } from '@aegisos/types';

export const RootConfigSchema = z.object({
  app: AppConfigSchema.default({}),
  runtime: RuntimeConfigSchema.default({}),
  ai: AIProviderConfigSchema.default({}),
  identity: IdentityProviderConfigSchema.default({}),
  storage: StorageProviderConfigSchema.default({}),
  db: DatabaseConfigSchema.default({}),
  queue: QueueConfigSchema.default({}),
  cache: CacheConfigSchema.default({}),
  security: SecurityConfigSchema.default({}),
  features: FeatureFlagConfigSchema.default({}),
});

export type RootConfig = DeepReadonly<z.infer<typeof RootConfigSchema>>;
