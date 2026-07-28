import { describe, it, expect } from 'vitest';
import { database_PLACEHOLDER } from '../src';

describe('database placeholder', () => {
  it('should be a placeholder', () => {
    expect(database_PLACEHOLDER).toBe(true);
  });
});
