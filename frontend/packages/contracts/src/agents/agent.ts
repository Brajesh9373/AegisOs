import { z } from 'zod';
import { BaseEntitySchema, MetadataSchema } from '../core/base';

export const AgentRoleSchema = z.enum(['Worker', 'Manager', 'Architect', 'Auditor']);
export type AgentRole = z.infer<typeof AgentRoleSchema>;

export const AgentStatusSchema = z.enum([
  'Idle',
  'Assigned',
  'Planning',
  'Waiting',
  'Executing',
  'Validating',
  'Blocked',
  'Approval Pending',
  'Retrying',
  'Completed',
  'Failed',
  'Cancelled',
  'Archived',
]);
export type AgentStatus = z.infer<typeof AgentStatusSchema>;

export const DigitalEmployeeSchema = BaseEntitySchema.extend({
  type: z.literal('DigitalEmployee'),
  name: z.string(),
  humanOwnerId: z.string().uuid(),
  managerId: z.string().uuid(),
  organizationId: z.string().uuid(),
  approvalAuthorityThreshold: z.number().int().optional(),
  role: AgentRoleSchema,
  department: z.string(),
  status: AgentStatusSchema,
  skills: z.array(z.string().uuid()).describe('IDs of assigned skills'),
  tools: z.array(z.string().uuid()).describe('IDs of assigned tools'),
  metadata: MetadataSchema.optional(),
});
export type DigitalEmployee = z.infer<typeof DigitalEmployeeSchema>;

export const DigitalManagerSchema = BaseEntitySchema.extend({
  type: z.literal('DigitalManager'),
  name: z.string(),
  department: z.string(),
  subordinateTeams: z.array(z.string().uuid()).describe('IDs of managed digital teams'),
});
export type DigitalManager = z.infer<typeof DigitalManagerSchema>;

export const DigitalTeamSchema = BaseEntitySchema.extend({
  type: z.literal('DigitalTeam'),
  name: z.string(),
  managerId: z.string().uuid().describe('ID of the DigitalManager overseeing this team'),
  members: z.array(z.string().uuid()).describe('IDs of DigitalEmployees in this team'),
});
export type DigitalTeam = z.infer<typeof DigitalTeamSchema>;
