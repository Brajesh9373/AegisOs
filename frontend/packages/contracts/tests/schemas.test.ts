import { describe, it, expect } from 'vitest';
import { BaseEntitySchema } from '../src/core/base';
import { DigitalEmployeeSchema } from '../src/agents/agent';

describe('Contracts Schema Validation', () => {
  it('should validate a valid BaseEntity', () => {
    const valid = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      createdAt: '2026-07-03T12:00:00Z',
      updatedAt: '2026-07-03T12:00:00Z',
    };
    expect(BaseEntitySchema.safeParse(valid).success).toBe(true);
  });

  it('should reject an invalid UUID', () => {
    const invalid = {
      id: 'not-a-uuid',
      createdAt: '2026-07-03T12:00:00Z',
      updatedAt: '2026-07-03T12:00:00Z',
    };
    expect(BaseEntitySchema.safeParse(invalid).success).toBe(false);
  });

  it('should validate a valid DigitalEmployee', () => {
    const valid = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      createdAt: '2026-07-03T12:00:00Z',
      updatedAt: '2026-07-03T12:00:00Z',
      type: 'DigitalEmployee',
      name: 'Agent Alpha',
      role: 'Worker',
      humanOwnerId: '123e4567-e89b-12d3-a456-426614174000',
      managerId: '123e4567-e89b-12d3-a456-426614174001',
      organizationId: '123e4567-e89b-12d3-a456-426614174002',
      department: 'Engineering',
      status: 'Idle',
      skills: [],
      tools: [],
    };
    expect(DigitalEmployeeSchema.safeParse(valid).success).toBe(true);
  });
});
