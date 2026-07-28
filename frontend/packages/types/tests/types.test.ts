import { describe, it, expectTypeOf, expect } from 'vitest';
import { DeepPartial, OmitMetadata, Mutable, Result, ok, fail } from '../src';
import type { DigitalEmployee } from '@aegisos/contracts';

describe('Type Utilities', () => {
  it('should omit metadata correctly', () => {
    type CreatePayload = OmitMetadata<DigitalEmployee>;

    // Type-level assertion
    expectTypeOf<CreatePayload>().not.toHaveProperty('id');
    expectTypeOf<CreatePayload>().not.toHaveProperty('createdAt');
    expectTypeOf<CreatePayload>().not.toHaveProperty('updatedAt');
    expectTypeOf<CreatePayload>().toHaveProperty('name');
  });

  it('should support DeepPartial', () => {
    type PartialEmployee = DeepPartial<DigitalEmployee>;
    expectTypeOf<PartialEmployee>().toMatchTypeOf<{ name?: string }>();
  });
});

describe('Monadic Result', () => {
  it('ok() creates a success result', () => {
    const res: Result<string> = ok('success');
    expect(res.success).toBe(true);
    if (res.success) {
      expect(res.value).toBe('success');
    }
  });

  it('fail() creates a failure result', () => {
    const res: Result<string> = fail(new Error('error'));
    expect(res.success).toBe(false);
    if (!res.success) {
      expect(res.error.message).toBe('error');
    }
  });
});
