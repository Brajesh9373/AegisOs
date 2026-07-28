import { z } from 'zod';
import { BaseEntitySchema, MetadataSchema } from '../core/base';

export const ExecutionStatusSchema = z.enum([
  'Pending',
  'Running',
  'Suspended',
  'Completed',
  'Failed',
  'RolledBack',
]);
export type ExecutionStatus = z.infer<typeof ExecutionStatusSchema>;

export const ActionSchema = BaseEntitySchema.extend({
  taskId: z.string().uuid(),
  toolId: z.string().uuid(),
  inputPayload: z.record(z.string(), z.unknown()),
  outputPayload: z.record(z.string(), z.unknown()).optional(),
  status: ExecutionStatusSchema,
});
export type Action = z.infer<typeof ActionSchema>;

export const TaskSchema = BaseEntitySchema.extend({
  workflowId: z.string().uuid(),
  skillId: z.string().uuid(),
  assignedAgentId: z.string().uuid().optional(),
  status: ExecutionStatusSchema,
  dependencies: z.array(z.string().uuid()).describe('IDs of Tasks that must complete first'),
  retryCount: z.number().int().min(0).default(0),
});
export type Task = z.infer<typeof TaskSchema>;

export const WorkflowSchema = BaseEntitySchema.extend({
  name: z.string(),
  description: z.string(),
  status: ExecutionStatusSchema,
  tasks: z.array(TaskSchema),
  metadata: MetadataSchema.optional(),
});
export type Workflow = z.infer<typeof WorkflowSchema>;
