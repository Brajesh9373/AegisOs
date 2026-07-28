import { describe, it, expect, beforeEach } from 'vitest';
import { loadConfiguration, ConfigurationRegistry, ConfigurationFactory } from '../src';
import { isSuccess, unwrap } from '@aegisos/shared';

describe('Configuration Layer', () => {
  beforeEach(() => {
    ConfigurationRegistry._reset();
    process.env = {}; // Clear env for deterministic testing
  });

  it('should load default configuration from empty env', () => {
    const res = loadConfiguration();
    expect(isSuccess(res)).toBe(true);
    if (isSuccess(res)) {
      const config = res.value;
      expect(config.app.name).toBe('aegisOS');
      expect(config.app.environment).toBe('development');
      expect(config.ai.defaultModel).toBe('gpt-4');
      expect(config.db.poolMin).toBe(2);
    }
  });

  it('should fail on invalid enum environment variable', () => {
    process.env.NODE_ENV = 'invalid_env';
    const res = loadConfiguration();
    expect(isSuccess(res)).toBe(false);
  });

  it('ConfigurationRegistry should throw if accessed before set', () => {
    expect(() => ConfigurationRegistry.get()).toThrowError(
      /Configuration has not been initialized/,
    );
  });

  it('ConfigurationRegistry should enforce singleton immutability', () => {
    const res = loadConfiguration();
    const config = unwrap(res);

    ConfigurationRegistry.set(config);
    expect(ConfigurationRegistry.get()).toBeDefined();

    expect(() => ConfigurationRegistry.set(config)).toThrowError(/already been initialized/);
  });

  it('ConfigurationFactory should create valid partial overrides', () => {
    const res = ConfigurationFactory.create({
      app: { name: 'TestApp' },
    });
    expect(isSuccess(res)).toBe(true);
    if (isSuccess(res)) {
      expect(res.value.app.name).toBe('TestApp');
      expect(res.value.app.environment).toBe('development'); // default retained
    }
  });
});
