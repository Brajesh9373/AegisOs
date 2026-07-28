import { describe, it, expect } from 'vitest';
import { ui_PLACEHOLDER } from '../src';

describe('ui placeholder', () => {
  it('should be a placeholder', () => {
    expect(ui_PLACEHOLDER).toBe(true);
  });
});
