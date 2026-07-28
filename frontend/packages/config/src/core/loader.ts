import { config } from 'dotenv';
import { Result, ok, fail } from '@aegisos/types';
import { ConfigurationError } from './errors';
import { RootConfigSchema, RootConfig } from '../schemas';
import { EnvironmentSchema } from '@aegisos/contracts';

/**
 * Loads configuration from process.env and validates it against the RootConfigSchema.
 */
export function loadConfiguration(): Result<RootConfig, ConfigurationError> {
  // Load .env variables into process.env if present
  config();

  // Attempt to parse features flag which might be JSON in ENV
  let features = {};
  if (process.env.FEATURE_FLAGS) {
    try {
      features = JSON.parse(process.env.FEATURE_FLAGS);
    } catch (e) {
      void e;
      // Ignore parse failure during raw load, let schema catch it
    }
  }

  const rawConfig = {
    app: {
      name: process.env.APP_NAME,
      version: process.env.APP_VERSION,
      environment: process.env.NODE_ENV as any,
    },
    runtime: {
      logLevel: process.env.LOG_LEVEL,
      telemetryEnabled: process.env.TELEMETRY_ENABLED === 'true',
      gracefulShutdownMs: process.env.GRACEFUL_SHUTDOWN_MS
        ? parseInt(process.env.GRACEFUL_SHUTDOWN_MS, 10)
        : undefined,
    },
    ai: {
      defaultModel: process.env.AI_DEFAULT_MODEL,
      openaiApiKey: process.env.OPENAI_API_KEY,
      anthropicApiKey: process.env.ANTHROPIC_API_KEY,
      temperature: process.env.AI_TEMPERATURE ? parseFloat(process.env.AI_TEMPERATURE) : undefined,
    },
    identity: {
      issuer: process.env.IDENTITY_ISSUER,
      clientId: process.env.IDENTITY_CLIENT_ID,
      clientSecret: process.env.IDENTITY_CLIENT_SECRET,
    },
    storage: {
      provider: process.env.STORAGE_PROVIDER,
      bucketName: process.env.STORAGE_BUCKET,
      basePath: process.env.STORAGE_BASE_PATH,
    },
    db: {
      url: process.env.DATABASE_URL,
      poolMin: process.env.DATABASE_POOL_MIN
        ? parseInt(process.env.DATABASE_POOL_MIN, 10)
        : undefined,
      poolMax: process.env.DATABASE_POOL_MAX
        ? parseInt(process.env.DATABASE_POOL_MAX, 10)
        : undefined,
    },
    queue: {
      redisUrl: process.env.REDIS_URL,
      concurrency: process.env.QUEUE_CONCURRENCY
        ? parseInt(process.env.QUEUE_CONCURRENCY, 10)
        : undefined,
    },
    cache: {
      enabled: process.env.CACHE_ENABLED !== 'false',
      ttlSeconds: process.env.CACHE_TTL ? parseInt(process.env.CACHE_TTL, 10) : undefined,
      redisUrl: process.env.REDIS_URL,
    },
    security: {
      corsOrigins: process.env.CORS_ORIGINS ? process.env.CORS_ORIGINS.split(',') : undefined,
      jwtSecret: process.env.JWT_SECRET,
    },
    features,
  };

  const parsed = RootConfigSchema.safeParse(rawConfig);

  if (!parsed.success) {
    return fail(
      new ConfigurationError('Configuration validation failed', { issues: parsed.error.issues }),
    );
  }

  return ok(parsed.data as RootConfig);
}
