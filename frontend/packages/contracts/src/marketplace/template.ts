import { z } from 'zod';
import { BaseEntitySchema, MetadataSchema } from '../core/base';
import { WorkflowSchema } from '../execution/workflow';
import { AgentRoleSchema } from '../agents/agent';

export const ImplementationTemplateSchema = BaseEntitySchema.extend({
  name: z.string(),
  version: z.string(),
  description: z.string(),
  requiredRoles: z.array(AgentRoleSchema),
  requiredSkills: z.array(z.string().uuid()),
  workflowTemplate: WorkflowSchema,
  metadata: MetadataSchema.optional(),
});
export type ImplementationTemplate = z.infer<typeof ImplementationTemplateSchema>;

export const ImplementationProjectSchema = BaseEntitySchema.extend({
  name: z.string(),
  templateId: z.string().uuid(),
  status: z.enum(['Draft', 'Active', 'Completed', 'Failed']),
  assignedTeamId: z.string().uuid(),
  progress: z.number().min(0).max(100),
});
export type ImplementationProject = z.infer<typeof ImplementationProjectSchema>;
