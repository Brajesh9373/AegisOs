/**
 * Reusable enterprise-grade utility types for the aegisOS Platform.
 */

/**
 * Deeply makes all properties of an object optional.
 */
export type DeepPartial<T> = T extends object
  ? {
      [P in keyof T]?: DeepPartial<T[P]>;
    }
  : T;

/**
 * Deeply makes all properties of an object readonly.
 */
export type DeepReadonly<T> = T extends object
  ? {
      readonly [P in keyof T]: DeepReadonly<T[P]>;
    }
  : T;

/**
 * Makes all properties of an object mutable (removes readonly).
 */
export type Mutable<T> = {
  -readonly [P in keyof T]: T[P];
};

/**
 * Omits the standard BaseEntity metadata (id, createdAt, updatedAt) from a type.
 * Highly useful for creation payloads (DTOs) before saving to a database.
 */
export type OmitMetadata<T> = Omit<T, 'id' | 'createdAt' | 'updatedAt'>;

/**
 * Requires at least one property of an object to be present.
 */
export type RequireAtLeastOne<T, Keys extends keyof T = keyof T> = Pick<T, Exclude<keyof T, Keys>> &
  {
    [K in Keys]-?: Required<Pick<T, K>> & Partial<Pick<T, Exclude<Keys, K>>>;
  }[Keys];

/**
 * Extracts the awaited return type of an asynchronous function.
 */
export type AsyncReturnType<T extends (...args: any) => Promise<any>> = T extends (
  ...args: any
) => Promise<infer R>
  ? R
  : any;
