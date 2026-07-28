import { describe, it, expectTypeOf } from 'vitest';
import type { JsonValue, Opaque, DeepPartial, DeepReadonly, PromiseOrValue, IsEqual } from '../src';

describe('Type Tests', () => {
  it('should validate JsonValue', () => {
    expectTypeOf<{ a: 1 }>().toMatchTypeOf<JsonValue>();
    expectTypeOf<number>().toMatchTypeOf<JsonValue>();
    expectTypeOf<string>().toMatchTypeOf<JsonValue>();
    expectTypeOf<boolean>().toMatchTypeOf<JsonValue>();
    expectTypeOf<null>().toMatchTypeOf<JsonValue>();
    expectTypeOf<JsonValue[]>().toMatchTypeOf<JsonValue>();
  });

  it('should validate Opaque', () => {
    type UserId = Opaque<string, 'UserId'>;
    expectTypeOf<UserId>().toMatchTypeOf<string>();
  });

  it('should validate DeepPartial', () => {
    interface User {
      profile: { name: string; age: number };
    }
    expectTypeOf<{ profile: { name: string } }>().toMatchTypeOf<DeepPartial<User>>();
    expectTypeOf<{ profile?: { name?: string; age?: number } }>().toMatchTypeOf<
      DeepPartial<User>
    >();
  });

  it('should validate DeepReadonly', () => {
    interface User {
      profile: { name: string; age: number };
    }
    type ReadonlyUser = DeepReadonly<User>;
    expectTypeOf<ReadonlyUser['profile']>().toMatchTypeOf<{
      readonly name: string;
      readonly age: number;
    }>();
  });

  it('should validate PromiseOrValue', () => {
    expectTypeOf<string>().toMatchTypeOf<PromiseOrValue<string>>();
    expectTypeOf<Promise<string>>().toMatchTypeOf<PromiseOrValue<string>>();
  });

  it('should validate IsEqual', () => {
    expectTypeOf<IsEqual<string, string>>().toMatchTypeOf<true>();
    expectTypeOf<IsEqual<string, number>>().toMatchTypeOf<false>();
  });
});
