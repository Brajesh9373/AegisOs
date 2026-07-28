import { describe, it, expect } from 'vitest';
import { guardian_PLACEHOLDER } from '../src';

describe('guardian placeholder', () => {
  it('should be a placeholder', () => {
    expect(guardian_PLACEHOLDER).toBe(true);
  });
});
