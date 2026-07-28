import { describe, it, expect } from 'vitest';
import {
  generateId,
  currentIsoTimestamp,
  safeJsonParse,
  isSuccess,
  unwrap,
  PlatformError,
} from '../src';
import { ok, fail } from '@aegisos/types';

describe('Shared Utilities', () => {
  it('generateId should return a valid UUID', () => {
    const id = generateId();
    expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
  });

  it('currentIsoTimestamp should return a valid ISO 8601 string', () => {
    const ts = currentIsoTimestamp();
    expect(!isNaN(Date.parse(ts))).toBe(true);
  });

  it('safeJsonParse should correctly parse valid JSON', () => {
    const res = safeJsonParse<{ test: boolean }>('{"test": true}');
    expect(isSuccess(res)).toBe(true);
    if (isSuccess(res)) {
      expect(res.value.test).toBe(true);
    }
  });

  it('safeJsonParse should gracefully handle invalid JSON', () => {
    const res = safeJsonParse('{"test": true'); // missing closing brace
    expect(isSuccess(res)).toBe(false);
  });

  it('unwrap should return value on ok', () => {
    const res = ok('val');
    expect(unwrap(res)).toBe('val');
  });

  it('unwrap should throw on fail', () => {
    const res = fail(new Error('fail'));
    expect(() => unwrap(res)).toThrow('fail');
  });

  it('PlatformError correctly captures code and metadata', () => {
    const err = new PlatformError('Test message', 'TEST_CODE', true, { key: 'val' });
    expect(err.message).toBe('Test message');
    expect(err.code).toBe('TEST_CODE');
    expect(err.metadata?.key).toBe('val');
  });
});
